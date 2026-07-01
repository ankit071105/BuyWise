"""
BuyWise Background Scheduler
============================
Runs periodic tasks:
1. Re-scrape all tracked products every hour (builds price history)
2. Check festival calendar and fire festival sale alerts
3. Trigger price drop alerts when target hit

Started automatically when FastAPI app boots.
Uses APScheduler (lighter than Celery, no Redis needed).
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models.models import TrackedProduct, Product, PriceHistory, Alert, User, BuyScore
from app.services.scraper import scrape_product
from app.ml.predictor import compute_buy_score, predict_price_trend

scheduler = AsyncIOScheduler()


# ============================================================
# FESTIVAL CALENDAR — India-specific
# ============================================================
FESTIVAL_WINDOWS = [
    {"name": "Republic Day Sale", "start": (1, 20), "end": (1, 27), "type": "electronics_fashion"},
    {"name": "Summer Sale", "start": (5, 15), "end": (5, 31), "type": "appliances"},
    {"name": "Independence Day Sale", "start": (8, 10), "end": (8, 20), "type": "general"},
    {"name": "Big Billion Days / Great Indian Festival", "start": (10, 1), "end": (10, 15), "type": "all"},
    {"name": "Diwali Sale", "start": (10, 20), "end": (11, 5), "type": "all"},
    {"name": "Year-End Sale", "start": (12, 20), "end": (12, 31), "type": "all"},
]


def get_active_festival() -> dict:
    """Returns the currently active festival (if any) or None"""
    today = datetime.now()
    m, d = today.month, today.day
    for f in FESTIVAL_WINDOWS:
        sm, sd = f["start"]
        em, ed = f["end"]
        if sm == m and d >= sd:
            return f
        if em == m and d <= ed:
            return f
        if sm != em and sm < m < em:
            return f
    return None


def get_upcoming_festival(days_ahead: int = 15) -> dict:
    """Returns festival within next N days if any"""
    today = datetime.now()
    for f in FESTIVAL_WINDOWS:
        sm, sd = f["start"]
        try:
            festival_start = datetime(today.year, sm, sd)
            if festival_start < today:
                festival_start = datetime(today.year + 1, sm, sd)
            days_diff = (festival_start - today).days
            if 0 <= days_diff <= days_ahead:
                return {**f, "days_away": days_diff}
        except:
            pass
    return None


# ============================================================
# HOURLY PRICE UPDATE JOB
# ============================================================

async def update_tracked_prices():
    """Re-scrape all actively tracked products, build price history"""
    print(f"[BuyWise Scheduler] Starting hourly price update at {datetime.utcnow()}")
    db = SessionLocal()
    updated = 0
    alerts_fired = 0
    try:
        tracked = db.query(TrackedProduct).filter(TrackedProduct.is_active == True).all()
        for tp in tracked:
            product = tp.product
            if not product:
                continue
            try:
                result = await scrape_product(product.url)
                if not result.get("success") or not result.get("current_price"):
                    continue

                new_price = result["current_price"]
                old_price = product.current_price

                # Save price point
                ph = PriceHistory(
                    product_id=product.id,
                    price=new_price,
                    platform=product.platform
                )
                db.add(ph)
                product.current_price = new_price
                product.last_scraped = datetime.utcnow()
                db.commit()
                updated += 1

                # Check alerts for this product
                alerts = db.query(Alert).filter(
                    Alert.product_id == product.id,
                    Alert.user_id == tp.user_id,
                    Alert.is_active == True,
                    Alert.is_triggered == False,
                ).all()

                for alert in alerts:
                    triggered = False
                    if alert.alert_type == "price_drop":
                        if alert.threshold and new_price <= alert.threshold:
                            triggered = True
                        elif old_price and new_price <= old_price * 0.95:
                            triggered = True
                    elif alert.alert_type == "festival":
                        if get_active_festival():
                            triggered = True

                    if triggered:
                        alert.is_triggered = True
                        db.commit()
                        alerts_fired += 1
                        print(f"[Alert] Fired for user {tp.user_id}, product {product.id}: ₹{old_price} → ₹{new_price}")

                # Recompute Buy Score with new history
                history_records = db.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id
                ).order_by(PriceHistory.scraped_at).all()
                price_history = [{"price": h.price, "scraped_at": h.scraped_at.isoformat()} for h in history_records]

                prediction = predict_price_trend(price_history)
                score_data = compute_buy_score(new_price, price_history, [], prediction)

                bs = BuyScore(
                    product_id=product.id,
                    score=score_data["score"],
                    price_score=score_data.get("price_score"),
                    review_score=score_data.get("review_score"),
                    timing_score=score_data.get("timing_score"),
                    reasoning=score_data.get("reasoning"),
                    recommendation=score_data.get("recommendation"),
                    predicted_low_price=score_data.get("predicted_low_price"),
                    predicted_low_date=f"{score_data.get('predicted_low_days', 15)} days"
                )
                db.add(bs)
                db.commit()

            except Exception as e:
                print(f"[Scheduler Error] Product {product.id}: {e}")
                continue

        print(f"[BuyWise Scheduler] Updated {updated} products, fired {alerts_fired} alerts")
    except Exception as e:
        print(f"[Scheduler Error] {e}")
    finally:
        db.close()


# ============================================================
# FESTIVAL ALERT CHECK — runs daily at 10am
# ============================================================

async def check_festival_alerts():
    """Notify users of tracked products when major festival window opens"""
    upcoming = get_upcoming_festival(days_ahead=7)
    if not upcoming:
        return

    print(f"[BuyWise Scheduler] Festival alert: {upcoming['name']} in {upcoming['days_away']} days")
    db = SessionLocal()
    try:
        # Auto-create festival alerts for all actively tracked products
        tracked = db.query(TrackedProduct).filter(TrackedProduct.is_active == True).all()
        for tp in tracked:
            existing = db.query(Alert).filter(
                Alert.product_id == tp.product_id,
                Alert.user_id == tp.user_id,
                Alert.alert_type == "festival",
                Alert.is_active == True,
            ).first()
            if not existing:
                alert = Alert(
                    user_id=tp.user_id,
                    product_id=tp.product_id,
                    alert_type="festival",
                    channel="browser",
                    is_active=True,
                )
                db.add(alert)
                db.commit()
        print("[BuyWise Scheduler] Festival alerts seeded")
    finally:
        db.close()


# ============================================================
# SETUP
# ============================================================

def start_scheduler():
    """Start the background scheduler when FastAPI boots"""
    # Every hour: update tracked product prices
    scheduler.add_job(
        update_tracked_prices,
        CronTrigger(minute=0),
        id="hourly_price_update",
        replace_existing=True,
    )
    # Daily at 10am: check festival calendar
    scheduler.add_job(
        check_festival_alerts,
        CronTrigger(hour=10, minute=0),
        id="daily_festival_check",
        replace_existing=True,
    )
    scheduler.start()
    print("[BuyWise Scheduler] Started — hourly prices + daily festival check")


def stop_scheduler():
    scheduler.shutdown()
