"""
BuyWise Smart Features — SIH Differentiators
=============================================
Novel features that no competitor offers:

1. detect_price_manipulation()  — Fake discount detector
2. compute_regret_score()        — Return-risk predictor from reviews
3. compute_total_cost()          — True cost including delivery/EMI/returns
4. compute_sustainability_score() — Green shopping score
5. find_alternatives()           — Better-rated similar products
"""
import re
from typing import Optional
from datetime import datetime


# ============================================================
# 1. PRICE MANIPULATION DETECTOR
# ============================================================
# Novel: exposes fake "70% off" discounts where MRP was inflated

def detect_price_manipulation(current_price: float, original_price: Optional[float],
                                price_history: list, rating: Optional[float] = None) -> dict:
    """
    Detects the common e-commerce trick where sellers inflate MRP before sales
    to fake big discounts.

    Returns:
        - manipulation_detected: bool
        - claimed_discount_pct: what seller shows
        - real_discount_pct: what's actually true based on history
        - manipulation_score: 0-100 (higher = more suspicious)
        - verdict: human-readable warning
    """
    if not current_price or not original_price:
        return {
            "manipulation_detected": False,
            "claimed_discount_pct": 0,
            "real_discount_pct": 0,
            "manipulation_score": 0,
            "verdict": "Insufficient data to check",
        }

    claimed_discount = round((original_price - current_price) / original_price * 100, 1)

    manipulation_score = 0
    warnings = []

    # Signal 1: Claimed discount > 50% is suspicious
    if claimed_discount > 60:
        manipulation_score += 30
        warnings.append(f"claimed discount of {claimed_discount}% is unusually high")
    elif claimed_discount > 40:
        manipulation_score += 15

    # Signal 2: If we have history, is current price actually low vs history?
    if price_history and len(price_history) >= 3:
        prices = [p["price"] for p in price_history if p.get("price")]
        if prices:
            hist_max = max(prices)
            hist_avg = sum(prices) / len(prices)

            # Real discount = current vs historical average
            real_discount = round((hist_avg - current_price) / hist_avg * 100, 1) if hist_avg > 0 else 0

            # If MRP is way above historical max, that's price manipulation
            mrp_inflation = (original_price - hist_max) / hist_max * 100 if hist_max > 0 else 0
            if mrp_inflation > 30:
                manipulation_score += 40
                warnings.append(f"MRP is {mrp_inflation:.0f}% above historical max — likely inflated")

            # If claimed discount is way more than real discount
            if claimed_discount > real_discount + 20:
                manipulation_score += 30
                warnings.append(f"real discount is only {real_discount}% vs claimed {claimed_discount}%")

            return {
                "manipulation_detected": manipulation_score >= 40,
                "claimed_discount_pct": claimed_discount,
                "real_discount_pct": real_discount,
                "manipulation_score": min(manipulation_score, 100),
                "historical_avg": round(hist_avg, 2),
                "historical_max": round(hist_max, 2),
                "warnings": warnings,
                "verdict": _get_manipulation_verdict(manipulation_score, claimed_discount, real_discount),
            }

    # No history — use heuristics based on discount % + rating
    if rating and rating < 3.5 and claimed_discount > 50:
        manipulation_score += 25
        warnings.append("high discount + low rating pattern suggests desperation pricing")

    return {
        "manipulation_detected": manipulation_score >= 40,
        "claimed_discount_pct": claimed_discount,
        "real_discount_pct": None,
        "manipulation_score": min(manipulation_score, 100),
        "warnings": warnings,
        "verdict": _get_manipulation_verdict(manipulation_score, claimed_discount, None),
    }


def _get_manipulation_verdict(score, claimed, real):
    if score >= 60:
        return f"⚠️ Likely fake discount — the '{claimed}% off' claim doesn't match reality"
    elif score >= 40:
        return f"⚠️ Suspicious pricing — verify before buying"
    elif score >= 20:
        return f"Discount seems inflated but not clearly fake"
    else:
        return f"Discount appears genuine ({claimed}% off)"


# ============================================================
# 2. REGRET PREDICTOR — Return-risk from review text mining
# ============================================================
# Novel: mines reviews for return/regret keywords and builds a score

RETURN_KEYWORDS = [
    "returned", "return it", "sent it back", "sending back", "getting refund",
    "asking for refund", "requested return", "waste of money", "regret buying",
    "should not have bought", "wish I hadn't", "big mistake", "disappointed",
    "not worth", "false advertising", "misleading", "cheap quality",
]

SIZE_ISSUE_KEYWORDS = [
    "wrong size", "size issue", "too small", "too big", "doesn't fit",
    "size chart wrong", "runs small", "runs large",
]

QUALITY_ISSUE_KEYWORDS = [
    "broke after", "damaged on arrival", "defective", "stopped working",
    "poor quality", "cheap material", "flimsy", "fell apart",
]


def compute_regret_score(reviews: list) -> dict:
    """
    Analyze reviews for return/regret signals.
    Returns 0-10 regret risk score.

    Novel — no competitor does this.
    """
    if not reviews:
        return {
            "regret_score": None,
            "regret_risk": "unknown",
            "return_mentions": 0,
            "size_issues": 0,
            "quality_issues": 0,
            "top_regret_reasons": [],
            "verdict": "Not enough review data",
        }

    total_reviews = len(reviews)
    return_mentions = 0
    size_issues = 0
    quality_issues = 0
    regret_snippets = []

    for review in reviews:
        text = (review.get("text") or "").lower()

        return_count = sum(1 for kw in RETURN_KEYWORDS if kw in text)
        if return_count > 0:
            return_mentions += 1
            regret_snippets.append(review.get("text", "")[:120])

        if any(kw in text for kw in SIZE_ISSUE_KEYWORDS):
            size_issues += 1

        if any(kw in text for kw in QUALITY_ISSUE_KEYWORDS):
            quality_issues += 1

    # Compute regret score (0-10, higher = more risky)
    return_rate = (return_mentions / total_reviews) * 100 if total_reviews > 0 else 0
    quality_rate = (quality_issues / total_reviews) * 100 if total_reviews > 0 else 0
    size_rate = (size_issues / total_reviews) * 100 if total_reviews > 0 else 0

    # Score: weighted by return mentions primarily
    regret_score = min(10, (return_rate * 0.15) + (quality_rate * 0.08) + (size_rate * 0.05))
    regret_score = round(regret_score, 1)

    if regret_score >= 6:
        risk_label = "high"
        verdict = f"⚠️ High return risk — {return_mentions} of {total_reviews} reviews mention returning it"
    elif regret_score >= 3:
        risk_label = "moderate"
        verdict = f"Moderate return risk — some buyers reported issues"
    elif regret_score >= 1:
        risk_label = "low"
        verdict = f"Low return risk — most buyers seem satisfied"
    else:
        risk_label = "very_low"
        verdict = f"Very low return risk — reviews show buyer satisfaction"

    # Top regret reasons
    top_reasons = []
    if size_issues > 0:
        top_reasons.append(f"Size/fit issues ({size_issues} reviews)")
    if quality_issues > 0:
        top_reasons.append(f"Quality issues ({quality_issues} reviews)")
    if return_mentions > 0:
        top_reasons.append(f"Return mentions ({return_mentions} reviews)")

    return {
        "regret_score": regret_score,
        "regret_risk": risk_label,
        "return_mentions": return_mentions,
        "size_issues": size_issues,
        "quality_issues": quality_issues,
        "return_rate_pct": round(return_rate, 1),
        "top_regret_reasons": top_reasons,
        "sample_regret_reviews": regret_snippets[:3],
        "verdict": verdict,
    }


# ============================================================
# 3. TOTAL COST OF OWNERSHIP
# ============================================================
# Novel: shows TRUE cost including delivery, return risk, EMI

def compute_total_cost(current_price: float, platform: str, category: str = "general",
                        regret_score: Optional[float] = None,
                        original_price: Optional[float] = None) -> dict:
    """
    Compute true cost of ownership.
    Factors: delivery, EMI interest (if applicable), return handling cost.
    """
    if not current_price:
        return {"total_cost": None, "verdict": "Price unavailable"}

    breakdown = {"listed_price": current_price}

    # Delivery cost estimates by platform
    delivery_costs = {
        "amazon": 0 if current_price > 499 else 40,      # Amazon free above 499
        "flipkart": 0 if current_price > 500 else 40,
        "myntra": 0 if current_price > 799 else 99,      # Myntra higher threshold
        "ajio": 0 if current_price > 999 else 99,
        "meesho": 0,                                       # Meesho free delivery
        "snapdeal": 0 if current_price > 500 else 40,
        "croma": 0 if current_price > 2000 else 100,
    }
    delivery = delivery_costs.get(platform.lower(), 50)
    breakdown["delivery"] = delivery

    # Expected return cost (based on regret score)
    return_probability = 0
    if regret_score is not None:
        return_probability = min(regret_score / 20, 0.3)  # max 30% return probability
    else:
        return_probability = 0.08  # Industry avg ~8%

    expected_return_cost = current_price * return_probability * 0.15
    breakdown["expected_return_handling"] = round(expected_return_cost, 2)

    # If category is expensive (electronics), suggest EMI
    emi_interest = 0
    if current_price > 5000:
        # Assume 6-month EMI at ~1% monthly interest
        emi_interest = current_price * 0.06
        breakdown["potential_emi_interest_6mo"] = round(emi_interest, 2)

    true_cost = current_price + delivery + expected_return_cost
    true_cost_with_emi = true_cost + emi_interest

    # Cost per year (assuming 3-year lifecycle for electronics, 2-year for others)
    lifecycle_years = 3 if current_price > 10000 else (2 if current_price > 3000 else 1)
    cost_per_year = round(true_cost / lifecycle_years, 2)

    savings_visible = 0
    if original_price and original_price > current_price:
        savings_visible = original_price - current_price

    return {
        "listed_price": current_price,
        "true_cost_upfront": round(true_cost, 2),
        "true_cost_with_emi": round(true_cost_with_emi, 2),
        "cost_per_year": cost_per_year,
        "estimated_lifecycle_years": lifecycle_years,
        "breakdown": breakdown,
        "savings_from_discount": savings_visible,
        "verdict": _get_tco_verdict(current_price, true_cost, cost_per_year),
    }


def _get_tco_verdict(listed, true_cost, per_year):
    diff = true_cost - listed
    if diff < 100:
        return f"True cost is nearly identical to listed price (₹{true_cost:,.0f}). Good value."
    return f"True cost is ₹{true_cost:,.0f} — that's ₹{diff:,.0f} more than listed (delivery + return risk). Annual cost: ₹{per_year:,.0f}."


# ============================================================
# 4. SUSTAINABILITY SCORE
# ============================================================
# Novel: green shopping score for ESG-conscious buyers

BRAND_ESG_SCORES = {
    # Rough ESG scores based on public data (0-10)
    "apple": 7.5, "samsung": 6.5, "sony": 7.0, "lg": 6.8,
    "nike": 6.0, "adidas": 7.2, "puma": 6.8, "reebok": 5.5,
    "hp": 7.0, "dell": 7.2, "lenovo": 6.5, "asus": 6.0,
    "godrej": 7.5, "tata": 8.0, "reliance": 6.5,
    "amazon": 5.5, "flipkart": 6.0, "myntra": 6.0,
    "boat": 5.5, "nothing": 6.5, "oneplus": 6.0, "xiaomi": 5.5, "realme": 5.0,
    "unbranded": 3.0, "generic": 3.0,
}


def compute_sustainability_score(product_name: str, platform: str,
                                   price: Optional[float] = None) -> dict:
    """
    Compute sustainability/green score (0-10).
    Factors: brand ESG, packaging (platform), local sourcing, product durability signals.
    """
    name_lower = (product_name or "").lower()

    # Brand detection
    brand_score = 5.0
    detected_brand = None
    for brand, score in BRAND_ESG_SCORES.items():
        if brand in name_lower:
            brand_score = score
            detected_brand = brand.title()
            break

    # Platform packaging score (based on public reporting)
    platform_scores = {
        "amazon": 5.5,      # Excessive packaging historically
        "flipkart": 6.5,    # Better packaging reforms
        "myntra": 6.0,
        "meesho": 5.0,      # Longer supply chains
        "ajio": 6.5,
        "croma": 7.0,       # Physical stores reduce delivery footprint
        "snapdeal": 6.0,
    }
    platform_score = platform_scores.get(platform.lower(), 5.5)

    # Category signal from name
    category_score = 6.0
    if any(kw in name_lower for kw in ["organic", "sustainable", "eco", "recycled", "bamboo", "cotton"]):
        category_score = 8.5
    elif any(kw in name_lower for kw in ["fast fashion", "single-use", "disposable"]):
        category_score = 3.0
    elif any(kw in name_lower for kw in ["electronic", "plastic", "battery"]):
        category_score = 5.0

    # Composite score
    final_score = round((brand_score * 0.4) + (platform_score * 0.3) + (category_score * 0.3), 1)

    # Label
    if final_score >= 8:
        label = "🌱 Excellent — sustainable choice"
    elif final_score >= 6:
        label = "🌿 Good — decent green footprint"
    elif final_score >= 4:
        label = "🌾 Fair — moderate environmental impact"
    else:
        label = "⚠️ Poor — consider greener alternatives"

    return {
        "sustainability_score": final_score,
        "brand_esg_score": brand_score,
        "brand_detected": detected_brand,
        "platform_packaging_score": platform_score,
        "product_category_score": category_score,
        "label": label,
        "green_alternatives_suggested": final_score < 5,
    }


# ============================================================
# 5. ALTERNATIVE PRODUCTS FINDER
# ============================================================
# When a product's Buy Score is low, suggest better options

async def find_alternatives(product_name: str, current_platform: str,
                             current_price: float, buy_score: float) -> dict:
    """
    If Buy Score < 5, find better-rated alternatives at similar price.
    Uses the existing search_products_by_name from scraper.
    """
    from app.services.scraper import search_products_by_name, extract_search_keywords

    if buy_score >= 6:
        return {"triggered": False, "reason": "Buy Score is decent — alternatives not needed"}

    # Extract category keywords (drop specific model)
    keywords = extract_search_keywords(product_name)
    words = keywords.split()
    # Keep first 2 words (usually brand + category) to search for broader alternatives
    search_query = " ".join(words[:2]) if len(words) > 2 else keywords

    try:
        alternatives = await search_products_by_name(search_query)

        # Filter — within +/- 30% of current price, not the same product
        min_price = current_price * 0.7
        max_price = current_price * 1.3
        filtered = []
        for alt in alternatives:
            alt_price = alt.get("current_price")
            if not alt_price:
                continue
            if not (min_price <= alt_price <= max_price):
                continue
            # Skip if it's the same product
            if product_name.lower()[:30] in alt.get("name", "").lower():
                continue
            filtered.append(alt)

        # Sort by price + rating
        filtered.sort(key=lambda x: (x.get("current_price", float('inf')), -(x.get("rating") or 0)))

        return {
            "triggered": True,
            "search_query": search_query,
            "alternatives": filtered[:3],
            "verdict": f"Found {len(filtered)} alternatives — buy score of this product is only {buy_score}/10",
        }
    except Exception as e:
        return {"triggered": True, "error": str(e), "alternatives": []}


# ============================================================
# COMPOSITE: Run all smart features for a product
# ============================================================

async def compute_all_smart_features(product_data: dict, buy_score_data: dict,
                                       price_history: list, reviews: list) -> dict:
    """Run all smart features and return combined result"""
    current_price = product_data.get("current_price")
    original_price = product_data.get("original_price")
    platform = product_data.get("platform", "unknown")
    product_name = product_data.get("name", "")
    rating = product_data.get("rating")
    buy_score = buy_score_data.get("score", 5.0)

    # 1. Price manipulation
    price_manipulation = detect_price_manipulation(
        current_price, original_price, price_history, rating
    )

    # 2. Regret score
    regret = compute_regret_score(reviews or [])

    # 3. Total cost of ownership
    total_cost = compute_total_cost(
        current_price, platform,
        regret_score=regret.get("regret_score"),
        original_price=original_price
    )

    # 4. Sustainability
    sustainability = compute_sustainability_score(product_name, platform, current_price)

    # 5. Alternatives (async, only if buy score low)
    alternatives = None
    if buy_score < 5 and current_price:
        alternatives = await find_alternatives(product_name, platform, current_price, buy_score)

    return {
        "price_manipulation": price_manipulation,
        "regret_analysis": regret,
        "total_cost_of_ownership": total_cost,
        "sustainability": sustainability,
        "alternatives": alternatives,
    }
