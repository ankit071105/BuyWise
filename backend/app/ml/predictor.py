import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import joblib
import os

# ⚠️ NOTE: XGBoost model trains on your collected price_history data.
# On first run with no data, it returns a heuristic estimate.
# The more price data you collect, the better predictions get.

MODEL_PATH = "app/ml/price_model.pkl"


def extract_features(price_records: List[dict]) -> pd.DataFrame:
    """Convert price history records into ML features"""
    if not price_records:
        return pd.DataFrame()

    df = pd.DataFrame(price_records)
    df["scraped_at"] = pd.to_datetime(df["scraped_at"])
    df = df.sort_values("scraped_at")

    df["day_of_week"] = df["scraped_at"].dt.dayofweek
    df["month"] = df["scraped_at"].dt.month
    df["day_of_month"] = df["scraped_at"].dt.day
    df["days_since_start"] = (df["scraped_at"] - df["scraped_at"].min()).dt.days

    # Rolling stats
    df["price_7d_avg"] = df["price"].rolling(7, min_periods=1).mean()
    df["price_30d_avg"] = df["price"].rolling(30, min_periods=1).mean()
    df["price_7d_min"] = df["price"].rolling(7, min_periods=1).min()
    df["price_change"] = df["price"].pct_change().fillna(0)

    # Festival proximity (India-specific)
    # Diwali range: Oct-Nov, Big Billion Days: Oct, Republic Day sale: Jan
    df["festival_proximity"] = df["month"].apply(lambda m: 1 if m in [1, 8, 10, 11] else 0)

    return df


def predict_price_trend(price_records: List[dict], days_ahead: int = 30) -> dict:
    """
    Predict price trend for next N days.
    Uses XGBoost if model trained, else heuristic fallback.
    """
    if len(price_records) < 5:
        # Not enough data — return heuristic
        if price_records:
            current = price_records[-1]["price"]
            historical_min = min(r["price"] for r in price_records)
            return {
                "predicted_low": round(historical_min * 0.97, 2),
                "predicted_low_days": 15,
                "confidence": "low",
                "trend": "insufficient_data",
                "note": "Need more price history for accurate prediction. Currently using heuristic."
            }
        return {"predicted_low": None, "confidence": "none", "trend": "no_data"}

    df = extract_features(price_records)
    prices = df["price"].values
    current_price = prices[-1]
    historical_min = float(np.min(prices))
    historical_avg = float(np.mean(prices))
    price_std = float(np.std(prices))

    # Trend detection
    recent_avg = float(np.mean(prices[-7:])) if len(prices) >= 7 else current_price
    older_avg = float(np.mean(prices[:-7])) if len(prices) > 7 else current_price
    trend = "falling" if recent_avg < older_avg * 0.98 else ("rising" if recent_avg > older_avg * 1.02 else "stable")

    # Try loading trained XGBoost model
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            feature_cols = ["day_of_week", "month", "day_of_month", "price_7d_avg",
                           "price_30d_avg", "price_7d_min", "price_change", "festival_proximity"]
            last_row = df[feature_cols].iloc[-1:].values
            predicted = float(model.predict(last_row)[0])
            predicted_low = min(predicted, historical_min)
            confidence = "high"
        except:
            predicted_low = historical_min * 0.98
            confidence = "medium"
    else:
        # Heuristic prediction based on trend
        if trend == "falling":
            predicted_low = max(current_price * 0.90, historical_min * 0.95)
            predicted_low_days = 10
        elif trend == "stable":
            predicted_low = historical_min * 0.99
            predicted_low_days = 20
        else:  # rising
            predicted_low = historical_min
            predicted_low_days = 30
        confidence = "medium"

    # Estimate days to lowest price
    price_drop_threshold = current_price * 0.95
    days_to_low = 15  # default
    for i, p in enumerate(reversed(prices)):
        if p <= price_drop_threshold:
            days_to_low = max(7, 30 - i)
            break

    return {
        "predicted_low": round(predicted_low, 2),
        "predicted_low_days": days_to_low,
        "confidence": confidence,
        "trend": trend,
        "historical_min": round(historical_min, 2),
        "historical_avg": round(historical_avg, 2),
        "price_volatility": round(price_std / historical_avg * 100, 1) if historical_avg > 0 else 0
    }


def compute_buy_score(
    current_price: float,
    price_records: List[dict],
    reviews: List[dict],
    prediction: dict
) -> dict:
    """
    Compute the BuyWise Buy Score (0-10).
    Breakdown: Price Score (40%) + Review Score (35%) + Timing Score (25%)
    """
    # --- Price Score (0-10) ---
    price_score = 5.0
    if price_records and current_price:
        historical_min = min(r["price"] for r in price_records)
        historical_max = max(r["price"] for r in price_records)
        historical_avg = sum(r["price"] for r in price_records) / len(price_records)
        price_range = historical_max - historical_min

        if price_range > 0:
            # How close is current price to historical minimum?
            price_percentile = (historical_max - current_price) / price_range
            price_score = price_percentile * 10
        
        # Bonus if at or near all-time low
        if current_price <= historical_min * 1.02:
            price_score = min(10, price_score + 1.5)
        elif current_price >= historical_avg * 1.1:
            price_score = max(0, price_score - 2)

    price_score = round(min(10, max(0, price_score)), 1)

    # --- Review Score (0-10) ---
    review_score = 5.0
    fake_count = 0
    fit_signals = []
    sentiments = []

    if reviews:
        valid_reviews = [r for r in reviews if not r.get("is_suspicious", False)]
        fake_count = len(reviews) - len(valid_reviews)

        if valid_reviews:
            avg_rating = sum(r.get("rating", 3) for r in valid_reviews) / len(valid_reviews)
            review_score = (avg_rating / 5.0) * 8  # max 8 from ratings

            # Sentiment bonus
            sentiments = [r.get("sentiment_score", 0) for r in valid_reviews if r.get("sentiment_score") is not None]
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                review_score += avg_sentiment * 2  # max +2 from sentiment

            # Fit signals for shoes
            fit_signals = list(set([r.get("fit_signal") for r in valid_reviews if r.get("fit_signal")]))

        # Penalize for fake reviews
        fake_ratio = fake_count / len(reviews) if reviews else 0
        review_score -= fake_ratio * 3

    review_score = round(min(10, max(0, review_score)), 1)

    # --- Timing Score (0-10) ---
    timing_score = 5.0
    trend = prediction.get("trend", "stable")
    confidence = prediction.get("confidence", "low")

    if trend == "falling":
        timing_score = 7.5
    elif trend == "stable":
        timing_score = 5.5
    elif trend == "rising":
        timing_score = 3.0

    # Festival proximity boost
    current_month = datetime.now().month
    if current_month in [10, 11]:  # Diwali/Big Billion Days season
        timing_score += 1.5
    elif current_month in [1]:  # Republic Day sales
        timing_score += 1.0

    if confidence == "high":
        timing_score = min(10, timing_score + 0.5)

    timing_score = round(min(10, max(0, timing_score)), 1)

    # --- Composite Score ---
    final_score = round((price_score * 0.40) + (review_score * 0.35) + (timing_score * 0.25), 1)

    # Recommendation
    if final_score >= 7.5:
        recommendation = "buy"
        rec_label = "Great time to buy!"
    elif final_score >= 5.5:
        recommendation = "consider"
        rec_label = "Decent deal, but could be better"
    elif final_score >= 4.0:
        recommendation = "wait"
        rec_label = "Wait for a better price"
    else:
        recommendation = "avoid"
        rec_label = "Price is high or reviews are poor"

    # AI reasoning summary (structured, will be enriched by LLM agent)
    reasoning_parts = []
    if price_score >= 7:
        reasoning_parts.append(f"price is near historical low (score: {price_score}/10)")
    elif price_score <= 4:
        reasoning_parts.append(f"price is above average (score: {price_score}/10)")
    else:
        reasoning_parts.append(f"price is average (score: {price_score}/10)")

    if review_score >= 7:
        reasoning_parts.append(f"reviews are strong (score: {review_score}/10)")
    elif fake_count > 0:
        reasoning_parts.append(f"{fake_count} suspicious reviews detected")

    if fit_signals:
        reasoning_parts.append(f"fit note: {', '.join(fit_signals[:2])}")

    if trend == "falling":
        reasoning_parts.append("price trend is falling — good timing")
    elif trend == "rising":
        reasoning_parts.append("price trend is rising — consider waiting")

    reasoning = "; ".join(reasoning_parts).capitalize() + "."

    return {
        "score": final_score,
        "price_score": price_score,
        "review_score": review_score,
        "timing_score": timing_score,
        "recommendation": recommendation,
        "recommendation_label": rec_label,
        "reasoning": reasoning,
        "fake_review_count": fake_count,
        "fit_signals": fit_signals,
        "predicted_low_price": prediction.get("predicted_low"),
        "predicted_low_days": prediction.get("predicted_low_days"),
        "trend": trend,
    }
