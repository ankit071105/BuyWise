import re
from typing import List
from datetime import datetime

# Fit/size keywords for shoes specifically
FIT_KEYWORDS = {
    "runs small": ["runs small", "size up", "too tight", "smaller than expected", "narrow"],
    "runs large": ["runs large", "size down", "too loose", "bigger than expected", "wide"],
    "true to size": ["true to size", "perfect fit", "fits perfectly", "exact size", "fits as expected"],
    "narrow fit": ["narrow", "tight on wide feet", "not for wide feet"],
    "wide fit": ["wide", "good for wide feet", "roomy"],
}

FAKE_REVIEW_PATTERNS = [
    r"\b(amazing|excellent|perfect|wonderful|fantastic|outstanding)\b.*\b(amazing|excellent|perfect|wonderful|fantastic|outstanding)\b",
    r"i (love|like) (this|it) (so much|a lot|very much)",
    r"(best|greatest).*(ever|i've|ive).*(bought|purchased|used)",
    r"(highly recommend|must buy|must have).*(everyone|everybody|all)",
    r"five stars?|5 stars?|★★★★★",
]


def analyze_sentiment(text: str) -> float:
    """
    Simple rule-based sentiment scoring (-1 to 1).
    ⚠️ For production: replace with transformers pipeline or Groq call.
    Local: `pip install transformers` and use distilbert-base-uncased-finetuned-sst-2-english
    """
    positive_words = [
        "good", "great", "excellent", "amazing", "love", "perfect", "comfortable",
        "quality", "durable", "value", "recommend", "happy", "satisfied", "best", "nice"
    ]
    negative_words = [
        "bad", "poor", "terrible", "horrible", "waste", "cheap", "broke", "fake",
        "disappointed", "return", "refund", "worst", "defective", "damaged", "avoid"
    ]
    text_lower = text.lower()
    pos = sum(1 for w in positive_words if w in text_lower)
    neg = sum(1 for w in negative_words if w in text_lower)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 2)


def detect_fit_signal(text: str) -> str | None:
    """Detect sizing/fit mentions in review text"""
    text_lower = text.lower()
    for signal, keywords in FIT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return signal
    return None


def is_suspicious_review(text: str, rating: float, review_date: datetime | None = None,
                          all_dates: List[datetime] | None = None) -> bool:
    """
    Flag suspicious/fake reviews using:
    1. Pattern matching on generic positive language
    2. Rating-text mismatch
    3. Burst detection (many reviews on same day)
    """
    # Pattern-based fake detection
    for pattern in FAKE_REVIEW_PATTERNS:
        if re.search(pattern, text.lower()):
            if len(text) < 100:  # Short + generic = suspicious
                return True

    # Rating-text mismatch
    sentiment = analyze_sentiment(text)
    if rating >= 4.5 and sentiment < -0.2:
        return True  # High rating but negative text
    if rating <= 2.0 and sentiment > 0.3:
        return True  # Low rating but positive text

    # Burst detection
    if review_date and all_dates:
        same_day = sum(1 for d in all_dates if d and abs((d - review_date).total_seconds()) < 86400)
        if same_day > 10:  # More than 10 reviews in 24 hours = suspicious burst
            return True

    return False


def analyze_reviews(reviews: List[dict]) -> List[dict]:
    """Full review analysis pipeline"""
    if not reviews:
        return []

    dates = []
    for r in reviews:
        try:
            d = datetime.fromisoformat(r.get("review_date", "")) if r.get("review_date") else None
        except:
            d = None
        dates.append(d)

    analyzed = []
    for i, review in enumerate(reviews):
        text = review.get("text", "")
        rating = review.get("rating", 3.0)
        review_date = dates[i]

        sentiment = analyze_sentiment(text)
        fit_signal = detect_fit_signal(text)
        suspicious = is_suspicious_review(text, rating, review_date, dates)

        analyzed.append({
            **review,
            "sentiment_score": sentiment,
            "fit_signal": fit_signal,
            "is_suspicious": suspicious,
        })

    return analyzed


def get_review_summary(analyzed_reviews: List[dict]) -> dict:
    """Aggregate review insights"""
    if not analyzed_reviews:
        return {"total": 0, "fake_count": 0, "avg_sentiment": 0, "fit_summary": {}}

    fake = [r for r in analyzed_reviews if r.get("is_suspicious")]
    valid = [r for r in analyzed_reviews if not r.get("is_suspicious")]
    sentiments = [r["sentiment_score"] for r in valid if r.get("sentiment_score") is not None]
    avg_sentiment = round(sum(sentiments) / len(sentiments), 2) if sentiments else 0

    fit_counts = {}
    for r in valid:
        sig = r.get("fit_signal")
        if sig:
            fit_counts[sig] = fit_counts.get(sig, 0) + 1

    return {
        "total": len(analyzed_reviews),
        "valid_count": len(valid),
        "fake_count": len(fake),
        "fake_percentage": round(len(fake) / len(analyzed_reviews) * 100, 1),
        "avg_sentiment": avg_sentiment,
        "sentiment_label": "Positive" if avg_sentiment > 0.1 else ("Negative" if avg_sentiment < -0.1 else "Neutral"),
        "fit_summary": fit_counts,
        "dominant_fit": max(fit_counts, key=fit_counts.get) if fit_counts else None,
    }
