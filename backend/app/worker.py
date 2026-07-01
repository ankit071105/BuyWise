"""
BuyWise Celery Worker — Background Price Monitoring
====================================================
Runs periodic tasks to:
  - Re-scrape tracked products
  - Update price history
  - Fire alerts when target price is hit
  - Send Telegram notifications

Usage:
  celery -A app.worker worker --beat --loglevel=info

⚠️ Requires Redis: add REDIS_URL to .env
⚠️ Requires TELEGRAM_BOT_TOKEN for Telegram alerts
"""

import os
import asyncio
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

celery_app = Celery("buywise", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.beat_schedule = {
    # Check tracked products every 6 hours
    "check-prices-every-6h": {
        "task": "app.worker.check_all_tracked_products",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}
celery_app.conf.timezone = "Asia/Kolkata"


@celery_app.task(name="app.worker.check_all_tracked_products")
def check_all_tracked_products():
    """Re-scrape all actively tracked products and fire alerts"""
    from app.database import SessionLocal
    from app.models.models import TrackedProduct, Product, PriceHistory, Alert, User
    from app.services.scraper import scrape_product
    from app.ml.predictor import compute_buy_score, predict_price_trend
    from datetime import datetime

    db = SessionLocal()
    try:
        tracked = db.query(TrackedProduct).filter(TrackedProduct.is_active == True).all()
        print(f"[BuyWise Worker] Checking {len(tracked)} tracked products...")

        for tp in tracked:
            product = tp.product
            try:
                result = asyncio.run(scrape_product(product.url))
                if not result.get("success"):
                    continue

                new_price = result.get("current_price")
                if not new_price:
                    continue

                # Save new price point
                ph = PriceHistory(
                    product_id=product.id,
                    price=new_price,
                    platform=product.platform
                )
                db.add(ph)

                # Update product current price
                old_price = product.current_price
                product.current_price = new_price
                product.last_scraped = datetime.utcnow()
                db.commit()

                # Check alerts for this product+user
                alerts = db.query(Alert).filter(
                    Alert.product_id == product.id,
                    Alert.user_id == tp.user_id,
                    Alert.is_active == True,
                    Alert.is_triggered == False
                ).all()

                for alert in alerts:
                    triggered = False
                    if alert.alert_type == "price_drop" and alert.threshold:
                        if new_price <= alert.threshold:
                            triggered = True
                    elif alert.alert_type == "price_drop" and old_price:
                        # Any 5%+ drop
                        if new_price <= old_price * 0.95:
                            triggered = True

                    if triggered:
                        alert.is_triggered = True
                        db.commit()
                        user = db.query(User).filter(User.id == tp.user_id).first()
                        if user and alert.channel == "telegram" and user.telegram_id:
                            send_telegram_alert(
                                user.telegram_id,
                                product.name,
                                old_price,
                                new_price,
                                product.url
                            )
                        print(f"[Alert Fired] User {tp.user_id} | {product.name} | ₹{old_price} → ₹{new_price}")

            except Exception as e:
                print(f"[Worker Error] Product {product.id}: {e}")
                continue

        print("[BuyWise Worker] Price check complete ✅")
    finally:
        db.close()


def send_telegram_alert(chat_id: str, product_name: str, old_price: float, new_price: float, url: str):
    """Send Telegram notification on price drop"""
    if not TELEGRAM_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN not set — skipping Telegram alert")
        return

    import httpx
    drop_pct = round((old_price - new_price) / old_price * 100, 1)
    message = (
        f"🔥 *BuyWise Price Drop Alert!*\n\n"
        f"📦 {product_name}\n"
        f"💰 ₹{old_price:,.0f} → *₹{new_price:,.0f}* ({drop_pct}% off)\n\n"
        f"🛒 [Buy Now]({url})\n\n"
        f"_BuyWise — Smart Shopping AI_"
    )
    try:
        httpx.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"[Telegram Error] {e}")
