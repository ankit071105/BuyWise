from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.models import Product, PriceHistory, BuyScore, TrackedProduct, SearchHistory
from app.api.auth import get_current_user
from app.models.models import User
from app.agents.pipeline import run_pipeline
from app.services.scraper import auto_compare_platforms, scrape_product

router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    query: Optional[str] = None


class TrackRequest(BaseModel):
    product_id: int
    target_price: Optional[float] = None


class CompareRequest(BaseModel):
    """
    Two modes:
    - auto: pass just `url` — we scrape it + auto-search other platform
    - manual: pass `amazon_url` AND `flipkart_url`
    """
    url: Optional[str] = None
    amazon_url: Optional[str] = None
    flipkart_url: Optional[str] = None


def save_product_and_price(db: Session, product_data: dict) -> Product:
    url = product_data.get("url", "")
    existing = db.query(Product).filter(Product.url == url).first()

    if not existing:
        existing = Product(
            name=product_data.get("name", "Unknown"),
            platform=product_data.get("platform", "unknown"),
            url=url,
            image_url=product_data.get("image_url"),
            current_price=product_data.get("current_price"),
            original_price=product_data.get("original_price"),
            rating=product_data.get("rating"),
            review_count=product_data.get("review_count", 0),
            last_scraped=datetime.utcnow()
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)
    else:
        existing.current_price = product_data.get("current_price") or existing.current_price
        existing.last_scraped = datetime.utcnow()
        if product_data.get("image_url"):
            existing.image_url = product_data.get("image_url")
        db.commit()

    if product_data.get("current_price"):
        ph = PriceHistory(
            product_id=existing.id,
            price=product_data["current_price"],
            platform=product_data.get("platform", "unknown")
        )
        db.add(ph)
        db.commit()

    return existing


def get_price_history(db: Session, product_id: int) -> list:
    records = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.scraped_at).all()
    return [{"price": h.price, "scraped_at": h.scraped_at.isoformat()} for h in records]


@router.post("/analyze")
def analyze_product(req: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not req.url and not req.query:
        raise HTTPException(status_code=400, detail="Provide either url or query")

    price_history = []
    existing_product = None
    if req.url:
        existing_product = db.query(Product).filter(Product.url == req.url).first()
        if existing_product:
            price_history = get_price_history(db, existing_product.id)

    result = run_pipeline(url=req.url, query=req.query, price_history=price_history)

    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("error", "Analysis failed"))

    product_data = result["product"]

    if product_data.get("name") and product_data.get("name") != "Unknown Product":
        saved_product = save_product_and_price(db, product_data)
        result["price_history"] = get_price_history(db, saved_product.id)

        if result.get("buy_score"):
            bs_data = result["buy_score"]
            bs = BuyScore(
                product_id=saved_product.id,
                score=bs_data["score"],
                price_score=bs_data.get("price_score"),
                review_score=bs_data.get("review_score"),
                timing_score=bs_data.get("timing_score"),
                reasoning=result.get("llm_reasoning"),
                recommendation=bs_data.get("recommendation"),
                predicted_low_price=bs_data.get("predicted_low_price"),
                predicted_low_date=str(bs_data.get("predicted_low_days", "")) + " days"
            )
            db.add(bs)
            db.commit()

        sh = SearchHistory(user_id=current_user.id, query=req.url or req.query, product_id=saved_product.id)
        db.add(sh)
        db.commit()
        result["product_id"] = saved_product.id
    else:
        sh = SearchHistory(user_id=current_user.id, query=req.url or req.query)
        db.add(sh)
        db.commit()

    return result


@router.post("/compare")
async def compare_prices(req: CompareRequest, current_user: User = Depends(get_current_user)):
    """
    Auto-compare: pass just ONE URL, we find the same product on the other platform automatically.
    """
    # Auto mode — user gives one URL, we find matches on other platform
    if req.url:
        result = await auto_compare_platforms(req.url)
        if not result.get("success"):
            raise HTTPException(status_code=422, detail=result.get("error", "Auto-compare failed"))
        return result

    # Manual mode — user gives both URLs
    if req.amazon_url or req.flipkart_url:
        import asyncio
        tasks = []
        if req.amazon_url:
            tasks.append(scrape_product(req.amazon_url))
        if req.flipkart_url:
            tasks.append(scrape_product(req.flipkart_url))
        scraped = await asyncio.gather(*tasks)

        options = []
        for data in scraped:
            if data.get("success"):
                options.append({
                    "name": data.get("name"),
                    "platform": data.get("platform"),
                    "url": data.get("url"),
                    "current_price": data.get("current_price"),
                    "original_price": data.get("original_price"),
                    "rating": data.get("rating"),
                    "image_url": data.get("image_url"),
                    "is_source": True
                })

        priced = [o for o in options if o.get("current_price")]
        if priced:
            best = min(priced, key=lambda x: x["current_price"])
            max_price = max(o["current_price"] for o in priced)
            for o in options:
                if o.get("current_price"):
                    o["savings"] = round(max_price - o["current_price"], 2)
                    o["savings_pct"] = round((max_price - o["current_price"]) / max_price * 100, 1) if max_price > 0 else 0
                    o["is_best"] = (o["current_price"] == best["current_price"])
            return {
                "success": True,
                "options": options,
                "best_platform": best["platform"],
                "best_price": best["current_price"],
                "recommendation": f"Buy from {best['platform'].title()} — cheapest at ₹{best['current_price']:,.0f}"
            }

        return {"success": True, "options": options, "recommendation": "Could not extract prices"}

    raise HTTPException(status_code=400, detail="Provide 'url' for auto-compare or 'amazon_url'/'flipkart_url' for manual")


@router.post("/track")
def track_product(req: TrackRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(TrackedProduct).filter(
        TrackedProduct.user_id == current_user.id,
        TrackedProduct.product_id == req.product_id
    ).first()

    if existing:
        existing.target_price = req.target_price
        existing.is_active = True
        db.commit()
        return {"message": "Tracking updated"}

    tp = TrackedProduct(user_id=current_user.id, product_id=req.product_id, target_price=req.target_price)
    db.add(tp)
    db.commit()
    return {"message": "Now tracking product"}


@router.get("/tracked")
def get_tracked_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tracked = db.query(TrackedProduct).filter(
        TrackedProduct.user_id == current_user.id,
        TrackedProduct.is_active == True
    ).all()

    result = []
    for t in tracked:
        product = t.product
        latest_score = db.query(BuyScore).filter(BuyScore.product_id == product.id).order_by(BuyScore.computed_at.desc()).first()
        price_history = get_price_history(db, product.id)
        result.append({
            "tracked_id": t.id,
            "target_price": t.target_price,
            "product": {
                "id": product.id, "name": product.name, "platform": product.platform,
                "url": product.url, "image_url": product.image_url,
                "current_price": product.current_price, "original_price": product.original_price,
                "rating": product.rating,
            },
            "buy_score": latest_score.score if latest_score else None,
            "recommendation": latest_score.recommendation if latest_score else None,
            "reasoning": latest_score.reasoning if latest_score else None,
            "price_history": price_history
        })
    return result


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    price_history = get_price_history(db, product_id)
    latest_score = db.query(BuyScore).filter(BuyScore.product_id == product_id).order_by(BuyScore.computed_at.desc()).first()

    return {
        "product": {
            "id": product.id, "name": product.name, "platform": product.platform,
            "url": product.url, "image_url": product.image_url,
            "current_price": product.current_price, "original_price": product.original_price,
            "rating": product.rating, "review_count": product.review_count,
        },
        "price_history": price_history,
        "buy_score": {
            "score": latest_score.score, "price_score": latest_score.price_score,
            "review_score": latest_score.review_score, "timing_score": latest_score.timing_score,
            "reasoning": latest_score.reasoning, "recommendation": latest_score.recommendation,
            "predicted_low_price": latest_score.predicted_low_price,
        } if latest_score else None
    }


@router.delete("/track/{tracked_id}")
def untrack_product(tracked_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tp = db.query(TrackedProduct).filter(TrackedProduct.id == tracked_id, TrackedProduct.user_id == current_user.id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="Not found")
    tp.is_active = False
    db.commit()
    return {"message": "Untracked"}