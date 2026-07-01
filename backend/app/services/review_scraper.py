"""
BuyWise Amazon Review Scraper — Deep review fetching
====================================================
Fetches real Amazon reviews by:
1. Scrolling the product page to load lazy reviews
2. Falling back to Amazon's /product-reviews/ page for more reviews
3. Extracting review text, rating, date, verified purchase flag
"""

import re
import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright
from urllib.parse import urlparse


def extract_asin(url: str) -> Optional[str]:
    """Extract Amazon ASIN from product URL"""
    m = re.search(r'/dp/([A-Z0-9]{10})', url) or re.search(r'/gp/product/([A-Z0-9]{10})', url)
    return m.group(1) if m else None


async def fetch_amazon_reviews_deep(url: str, max_reviews: int = 15) -> List[dict]:
    """
    Fetch real Amazon reviews by:
    1. Scrolling the product page to load lazy content
    2. Then hitting /product-reviews/ page for more
    """
    reviews = []
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
    )
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="en-IN",
    )
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """)

    try:
        page = await context.new_page()

        # Step 1: Product page with scroll to load reviews
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        # Scroll down slowly to trigger lazy loading of reviews
        for _ in range(6):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(0.6)

        # Try to click "See more reviews" if present
        try:
            await page.click("a[data-hook='see-all-reviews-link-foot']", timeout=2000)
            await asyncio.sleep(2)
        except:
            pass

        reviews_from_page = await page.evaluate("""() => {
            const out = [];
            const cards = document.querySelectorAll('[data-hook="review"]');
            for (let i = 0; i < Math.min(cards.length, 12); i++) {
                const card = cards[i];
                const body = card.querySelector('[data-hook="review-body"] span, [data-hook="review-body"]');
                const ratingEl = card.querySelector('i[data-hook="review-star-rating"] span, i[data-hook="cmps-review-star-rating"] span');
                const dateEl = card.querySelector('[data-hook="review-date"]');
                const verifiedEl = card.querySelector('[data-hook="avp-badge"]');
                const reviewerEl = card.querySelector('.a-profile-name');
                
                let rating = null;
                if (ratingEl) {
                    const m = ratingEl.innerText.match(/(\\d+\\.?\\d*)/);
                    if (m) rating = parseFloat(m[1]);
                }
                
                if (body && body.innerText.trim().length > 10) {
                    out.push({
                        text: body.innerText.trim().slice(0, 800),
                        rating: rating || 4.0,
                        reviewer: reviewerEl ? reviewerEl.innerText.trim() : 'Amazon Customer',
                        review_date: dateEl ? dateEl.innerText.trim() : null,
                        verified_purchase: !!verifiedEl,
                    });
                }
            }
            return out;
        }""")

        reviews.extend(reviews_from_page)

        # Step 2: If we don't have enough, hit the dedicated reviews page
        if len(reviews) < max_reviews:
            asin = extract_asin(url)
            if asin:
                reviews_url = f"https://www.amazon.in/product-reviews/{asin}/?ie=UTF8&reviewerType=all_reviews"
                try:
                    await page.goto(reviews_url, wait_until="domcontentloaded", timeout=25000)
                    await asyncio.sleep(2)
                    for _ in range(3):
                        await page.evaluate("window.scrollBy(0, 800)")
                        await asyncio.sleep(0.5)

                    more_reviews = await page.evaluate("""() => {
                        const out = [];
                        const cards = document.querySelectorAll('[data-hook="review"]');
                        for (let i = 0; i < Math.min(cards.length, 15); i++) {
                            const card = cards[i];
                            const body = card.querySelector('[data-hook="review-body"] span, [data-hook="review-body"]');
                            const ratingEl = card.querySelector('i[data-hook="review-star-rating"] span, i[data-hook="cmps-review-star-rating"] span');
                            const dateEl = card.querySelector('[data-hook="review-date"]');
                            const verifiedEl = card.querySelector('[data-hook="avp-badge"]');
                            const reviewerEl = card.querySelector('.a-profile-name');
                            
                            let rating = null;
                            if (ratingEl) {
                                const m = ratingEl.innerText.match(/(\\d+\\.?\\d*)/);
                                if (m) rating = parseFloat(m[1]);
                            }
                            
                            if (body && body.innerText.trim().length > 10) {
                                out.push({
                                    text: body.innerText.trim().slice(0, 800),
                                    rating: rating || 4.0,
                                    reviewer: reviewerEl ? reviewerEl.innerText.trim() : 'Amazon Customer',
                                    review_date: dateEl ? dateEl.innerText.trim() : null,
                                    verified_purchase: !!verifiedEl,
                                });
                            }
                        }
                        return out;
                    }""")

                    # Deduplicate by text
                    seen = {r["text"][:100] for r in reviews}
                    for r in more_reviews:
                        if r["text"][:100] not in seen:
                            reviews.append(r)
                            seen.add(r["text"][:100])
                            if len(reviews) >= max_reviews:
                                break
                except Exception as e:
                    print(f"[Reviews page fetch] {e}")

        await page.close()
        return reviews[:max_reviews]

    except Exception as e:
        print(f"[fetch_amazon_reviews_deep] {e}")
        return reviews
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()
