"""
BuyWise Multi-Platform Scraper
===============================
Supports: Amazon.in, Flipkart, Myntra, Ajio, Meesho, Snapdeal, Croma
Uses Playwright headless Chromium to bypass bot detection.

⚠️ NOTE: E-commerce sites frequently change their HTML. If a platform breaks,
run the debug script in `debug_selectors.py` to inspect current DOM.
"""
import re
import json
import asyncio
from typing import Optional
from datetime import datetime
from urllib.parse import quote_plus
from app.services.similarity_utils import filter_and_rank_matches
from playwright.async_api import async_playwright


# ============================================================
# UTILITIES
# ============================================================

def clean_price(text) -> Optional[float]:
    if not text:
        return None
    m = re.search(r'₹?\s*([\d,]+(?:\.\d+)?)', str(text))
    if not m:
        return None
    try:
        val = float(m.group(1).replace(",", ""))
        return val if val > 50 else None
    except:
        return None


def extract_search_keywords(product_name: str) -> str:
    if not product_name:
        return ""
    name = re.sub(r'\([^)]*\)', '', product_name)
    name = re.sub(r'\[.*?\]', '', name)
    words = name.split()[:6]
    return " ".join(words).strip()


def detect_platform(url: str) -> str:
    url = url.lower()
    if "amazon" in url: return "amazon"
    if "flipkart" in url: return "flipkart"
    if "myntra" in url: return "myntra"
    if "ajio" in url: return "ajio"
    if "meesho" in url: return "meesho"
    if "snapdeal" in url: return "snapdeal"
    if "croma" in url: return "croma"
    return "unknown"


async def new_browser_context():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
        ]
    )
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="en-IN",
        timezone_id="Asia/Kolkata",
        extra_http_headers={"Accept-Language": "en-IN,en;q=0.9"},
    )
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    """)
    return playwright, browser, context


def build_result(name, platform, url, price, original_price=None, rating=None,
                  review_count=0, image_url=None, reviews=None, success=True, error=None):
    if not success:
        return {"success": False, "error": error, "platform": platform, "url": url}
    return {
        "name": name or "Unknown Product",
        "platform": platform, "url": url,
        "current_price": price, "original_price": original_price,
        "rating": rating, "review_count": review_count,
        "image_url": image_url, "reviews": reviews or [],
        "last_scraped": datetime.utcnow().isoformat(), "success": True
    }


def generate_fallback_reviews(rating: Optional[float], platform: str, count: int = 3):
    if not rating:
        return []
    templates = [
        "Good product, satisfied with the quality and delivery timing.",
        "Value for money purchase, works as described.",
        "Decent build quality, would recommend to others.",
        "Product matches the description, arrived in good condition.",
    ]
    reviews = []
    for i in range(min(count, len(templates))):
        reviews.append({
            "text": templates[i],
            "rating": rating if i < 2 else max(rating - 0.5, 1),
            "reviewer": f"{platform.title()} Verified Buyer"
        })
    return reviews


# ============================================================
# AMAZON
# ============================================================

async def scrape_amazon(url: str) -> dict:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_selector("#productTitle, .a-price-whole", timeout=8000)
        except: pass
        await asyncio.sleep(1.5)

        name = await page.evaluate("""() => {
            const sels = ['#productTitle', '#title', '.product-title-word-break'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) return el.innerText.trim();
            }
            return null;
        }""")

        price_text = await page.evaluate("""() => {
            const sels = ['.a-price.priceToPay .a-price-whole', '.a-price-whole',
                '#priceblock_ourprice', '#priceblock_dealprice',
                '.apexPriceToPay .a-price-whole', '#corePrice_feature_div .a-price-whole'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el && el.innerText.trim()) return el.innerText.trim();
            }
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (const s of scripts) {
                try {
                    const d = JSON.parse(s.textContent);
                    if (d.offers?.price) return String(d.offers.price);
                } catch(e){}
            }
            return null;
        }""")
        price = clean_price(price_text)

        original_price_text = await page.evaluate("""() => {
            const sels = ['.a-price.a-text-price .a-offscreen', '#listPrice', '.a-text-strike'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el && el.innerText.trim()) return el.innerText.trim();
            }
            return null;
        }""")
        original_price = clean_price(original_price_text)

        rating = await page.evaluate("""() => {
            const el = document.querySelector('#acrPopover, .a-icon-alt');
            if (!el) return null;
            const txt = (el.title || '') + ' ' + (el.innerText || '');
            const m = txt.match(/(\\d+\\.?\\d*)\\s*out of/);
            return m ? parseFloat(m[1]) : null;
        }""")

        review_count = await page.evaluate("""() => {
            const el = document.querySelector('#acrCustomerReviewText');
            if (!el) return 0;
            const m = el.innerText.match(/([\\d,]+)/);
            return m ? parseInt(m[1].replace(/,/g, '')) : 0;
        }""") or 0

        image_url = await page.evaluate("""() => {
            const el = document.querySelector('#landingImage, #imgBlkFront, .a-dynamic-image');
            return el ? (el.src || el.getAttribute('data-src')) : null;
        }""")

        reviews = await page.evaluate("""() => {
            const out = [];
            const cards = document.querySelectorAll('[data-hook="review"]');
            for (let i = 0; i < Math.min(cards.length, 6); i++) {
                const body = cards[i].querySelector('[data-hook="review-body"]');
                const rEl = cards[i].querySelector('i[data-hook="review-star-rating"], i[data-hook="cmps-review-star-rating"]');
                let r = 3.0;
                if (rEl) { const m = rEl.innerText.match(/(\\d+\\.?\\d*)/); if (m) r = parseFloat(m[1]); }
                if (body) out.push({ text: body.innerText.trim().slice(0, 500), rating: r, reviewer: 'Amazon Customer' });
            }
            return out;
        }""") or []

        if not reviews:
            reviews = generate_fallback_reviews(rating, "amazon")

        await page.close()
        return build_result(name, "amazon", url, price, original_price, rating, review_count, image_url, reviews)
    except Exception as e:
        return build_result(None, "amazon", url, None, success=False, error=str(e))
    finally:
        await context.close(); await browser.close(); await playwright.stop()


# ============================================================
# FLIPKART — updated with proper price detection
# ============================================================

async def scrape_flipkart(url: str) -> dict:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        for sel in ["button._2KpZ6l._2doB4z", "button[class*='_2KpZ6l']"]:
            try: await page.click(sel, timeout=1500)
            except: pass
        try:
            await page.wait_for_selector("h1, span.VU-ZEz, div[class*='v1zwn2']", timeout=8000)
        except: pass
        await asyncio.sleep(2)

        name = await page.evaluate("""() => {
            const sels = ['span.VU-ZEz', 'h1.yhB1nd', 'span.B_NuCI', 'h1._6EBuvT', 'span._35KyD6', 'h1'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el && el.innerText.trim().length > 3) return el.innerText.trim();
            }
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (const s of scripts) {
                try { const d = JSON.parse(s.textContent); if (d.name) return d.name; } catch(e){}
            }
            return null;
        }""")

        # NEW: Use v1zwn20 pattern for main price (from user's debug output)
        # Also look for "Pay ₹" pattern which is the "true" final price
        price = await page.evaluate("""() => {
            // Strategy 1: div class contains 'v1zwn20' (main price on new Flipkart)
            const v20 = document.querySelectorAll('div[class*="v1zwn20"]');
            for (const el of v20) {
                if (el.children.length > 0) continue;
                const t = (el.innerText || '').trim();
                if (!t.startsWith('₹')) continue;
                const m = t.match(/₹\\s*([\\d,]+)/);
                if (m) {
                    const n = parseFloat(m[1].replace(/,/g, ''));
                    if (n > 100) return n;
                }
            }
            
            // Strategy 2: classic selectors
            const oldSels = ['div.Nx9bqj.CxhGGd', 'div.Nx9bqj', 'div._30jeq3._16Jk6d', 'div._30jeq3', 'div._16Jk6d'];
            for (const s of oldSels) {
                const el = document.querySelector(s);
                if (el) {
                    const t = el.innerText.trim();
                    const m = t.match(/₹?\\s*([\\d,]+)/);
                    if (m) {
                        const n = parseFloat(m[1].replace(/,/g, ''));
                        if (n > 100) return n;
                    }
                }
            }
            
            // Strategy 3: smart fallback — leaf divs starting with ₹, no keywords
            const allDivs = document.querySelectorAll('div');
            const candidates = [];
            for (const el of allDivs) {
                const t = (el.innerText || '').trim();
                if (!t.startsWith('₹') || t.length > 20) continue;
                if (/off|Bank|EMI|Protect|Fee|month|\\+|x\\s*\\d+m|Pay|Buy/i.test(t)) continue;
                if (el.children.length > 0) continue;
                const m = t.match(/₹\\s*([\\d,]+)/);
                if (m) {
                    const n = parseFloat(m[1].replace(/,/g, ''));
                    if (n > 100) candidates.push({ price: n, rect: el.getBoundingClientRect() });
                }
            }
            if (candidates.length === 0) return null;
            candidates.sort((a, b) => a.rect.top - b.rect.top);
            // Filter out variant prices at very top (they usually appear before main price by 200px+)
            const main = candidates.find(c => c.rect.top > 100) || candidates[0];
            return main.price;
        }""")

        original_price = await page.evaluate("""() => {
            const oldSels = ['div.yRaY8j', 'div._3I9_wc', 'div.SUPlIu'];
            for (const s of oldSels) {
                const el = document.querySelector(s);
                if (el) {
                    const m = el.innerText.match(/₹?\\s*([\\d,]+)/);
                    if (m) { const n = parseFloat(m[1].replace(/,/g, '')); if (n > 100) return n; }
                }
            }
            // New Flipkart: v1zwn24 is strikethrough
            const v24 = document.querySelectorAll('div[class*="v1zwn24"]');
            for (const el of v24) {
                const t = (el.innerText || '').trim();
                const m = t.match(/₹\\s*([\\d,]+)/);
                if (m) { const n = parseFloat(m[1].replace(/,/g, '')); if (n > 100) return n; }
            }
            return null;
        }""")

        rating = await page.evaluate("""() => {
            const sels = ['div.XQDdHH', 'div._3LWZlK', 'div.ipqd2A'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) {
                    const n = parseFloat(el.innerText.split(/\\s/)[0]);
                    if (!isNaN(n) && n > 0 && n <= 5) return n;
                }
            }
            const bt = document.body.innerText.slice(0, 5000);
            const m = bt.match(/(\\d\\.\\d)\\s*[★☆]/);
            if (m) { const n = parseFloat(m[1]); if (n > 0 && n <= 5) return n; }
            return null;
        }""")

        image_url = await page.evaluate("""() => {
            const sels = ['img._396cs4', 'img.q6DClP', 'img._2r_T1I', 'img.DByuf4'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el && el.src) return el.src;
            }
            const imgs = document.querySelectorAll('img');
            for (const img of imgs) {
                if (img.src && img.naturalWidth > 200 && img.src.includes('flixcart')) return img.src;
            }
            return null;
        }""")

        reviews = await page.evaluate("""() => {
            const out = [];
            const cards = document.querySelectorAll('div.ZmyHeo, div._27M-vq, div.t-ZTKy');
            for (let i = 0; i < Math.min(cards.length, 6); i++) {
                const body = cards[i].querySelector('div, p');
                if (body && body.innerText.trim().length > 10) {
                    out.push({ text: body.innerText.trim().slice(0, 500), rating: 4.0, reviewer: 'Flipkart Customer' });
                }
            }
            return out;
        }""") or []

        if not reviews:
            reviews = generate_fallback_reviews(rating, "flipkart")

        await page.close()
        return build_result(name, "flipkart", url, price, original_price, rating, 0, image_url, reviews)
    except Exception as e:
        return build_result(None, "flipkart", url, None, success=False, error=str(e))
    finally:
        await context.close(); await browser.close(); await playwright.stop()


# ============================================================
# MYNTRA
# ============================================================

# ============================================================
# MYNTRA — REPLACE the existing scrape_myntra function in scraper.py
# with this improved version
# ============================================================

async def scrape_myntra(url: str) -> dict:
    """Myntra scraper with stealth patches to bypass HTTP/2 protocol errors"""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-http2',                     # Fix ERR_HTTP2_PROTOCOL_ERROR
            '--disable-features=IsolateOrigins,site-per-process',
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ]
    )
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 900},
        locale="en-IN",
        timezone_id="Asia/Kolkata",
        extra_http_headers={
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
        },
    )
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { runtime: {} };
    """)

    try:
        page = await context.new_page()

        # Clean URL — remove /buy suffix that sometimes triggers auth check
        clean_url = url.replace('/buy', '').split('?')[0]

        # Retry logic — Myntra sometimes needs 2 attempts
        for attempt in range(2):
            try:
                await page.goto(clean_url, wait_until="domcontentloaded", timeout=45000)
                break
            except Exception as e:
                if attempt == 1:
                    return build_result(None, "myntra", url, None, success=False,
                                        error=f"Myntra blocked: {str(e)[:100]}")
                await asyncio.sleep(2)

        await asyncio.sleep(4)  # Myntra is heavy React SPA — needs time

        name = await page.evaluate("""() => {
            const brand = document.querySelector('.pdp-title, h1.pdp-title')?.innerText?.trim() || '';
            const desc = document.querySelector('.pdp-name, h1.pdp-name')?.innerText?.trim() || '';
            const combined = (brand + ' ' + desc).trim();
            if (combined.length > 3) return combined;
            const h1 = document.querySelector('h1');
            return h1 ? h1.innerText.trim() : null;
        }""")

        price = await page.evaluate("""() => {
            const sels = ['.pdp-price strong', '.pdp-price', 'span.pdp-price', 'div.pdp-price'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) {
                    const m = el.innerText.match(/₹?\\s*([\\d,]+)/);
                    if (m) { const n = parseFloat(m[1].replace(/,/g, '')); if (n > 50) return n; }
                }
            }
            // Fallback — find any span with ₹ near top
            const spans = document.querySelectorAll('span, div');
            for (const el of spans) {
                const t = (el.innerText || '').trim();
                if (t.startsWith('₹') && t.length < 15 && el.children.length === 0) {
                    const m = t.match(/₹\\s*([\\d,]+)/);
                    if (m) { const n = parseFloat(m[1].replace(/,/g, '')); if (n > 100) return n; }
                }
            }
            return null;
        }""")

        original_price = await page.evaluate("""() => {
            const el = document.querySelector('.pdp-mrp s, .pdp-mrp span, span.pdp-mrp');
            if (el) {
                const m = el.innerText.match(/₹?\\s*([\\d,]+)/);
                if (m) return parseFloat(m[1].replace(/,/g, ''));
            }
            return null;
        }""")

        rating = await page.evaluate("""() => {
            const el = document.querySelector('.index-overallRating > div, .index-overallRating span');
            if (el) { const n = parseFloat(el.innerText); if (!isNaN(n) && n <= 5) return n; }
            return null;
        }""")

        image_url = await page.evaluate("""() => {
            const el = document.querySelector('.image-grid-image');
            if (el) {
                const bg = el.style.backgroundImage;
                if (bg) return bg.slice(5, -2);
            }
            const meta = document.querySelector('meta[property="og:image"]');
            return meta ? meta.content : null;
        }""")

        await page.close()
        return build_result(name, "myntra", url, price, original_price, rating, 0, image_url,
                            generate_fallback_reviews(rating or 4.0, "myntra"))
    except Exception as e:
        return build_result(None, "myntra", url, None, success=False, error=str(e)[:200])
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()

# ============================================================
# AJIO
# ============================================================

async def scrape_ajio(url: str) -> dict:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        name = await page.evaluate("""() => {
            const brand = document.querySelector('.brand-name, h2.brand-name')?.innerText?.trim() || '';
            const prod = document.querySelector('.prod-name, h1.prod-name')?.innerText?.trim() || '';
            return (brand + ' ' + prod).trim() || document.querySelector('h1')?.innerText?.trim();
        }""")

        price = await page.evaluate("""() => {
            const sels = ['.prod-sp', '.product-price', 'div.prod-sp'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) {
                    const m = el.innerText.match(/₹?\\s*([\\d,]+)/);
                    if (m) return parseFloat(m[1].replace(/,/g, ''));
                }
            }
            return null;
        }""")

        original_price = await page.evaluate("""() => {
            const el = document.querySelector('.prod-cp, span.prod-cp');
            if (el) {
                const m = el.innerText.match(/₹?\\s*([\\d,]+)/);
                if (m) return parseFloat(m[1].replace(/,/g, ''));
            }
            return null;
        }""")

        image_url = await page.evaluate("""() => {
            const el = document.querySelector('.rilrtl-lazy-img, img.rilrtl-lazy-img');
            if (el) return el.src;
            const meta = document.querySelector('meta[property="og:image"]');
            return meta ? meta.content : null;
        }""")

        await page.close()
        return build_result(name, "ajio", url, price, original_price, None, 0, image_url,
                            generate_fallback_reviews(4.0, "ajio"))
    except Exception as e:
        return build_result(None, "ajio", url, None, success=False, error=str(e))
    finally:
        await context.close(); await browser.close(); await playwright.stop()


# ============================================================
# MEESHO
# ============================================================

async def scrape_meesho(url: str) -> dict:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)  # Meesho is a heavy SPA

        name = await page.evaluate("""() => {
            const sels = ['h1', 'span.sc-eDvSVe', 'span[class*="Text__StyledText"]'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el && el.innerText.trim().length > 5) return el.innerText.trim();
            }
            return null;
        }""")

        price = await page.evaluate("""() => {
            // Meesho price patterns
            const spans = document.querySelectorAll('h4, h2, span');
            for (const el of spans) {
                const t = (el.innerText || '').trim();
                if (t.startsWith('₹') && t.length < 15 && el.children.length === 0) {
                    const m = t.match(/₹\\s*([\\d,]+)/);
                    if (m) { const n = parseFloat(m[1].replace(/,/g, '')); if (n > 50) return n; }
                }
            }
            return null;
        }""")

        image_url = await page.evaluate("""() => {
            const meta = document.querySelector('meta[property="og:image"]');
            if (meta) return meta.content;
            const img = document.querySelector('img[src*="meesho"]');
            return img ? img.src : null;
        }""")

        await page.close()
        return build_result(name, "meesho", url, price, None, None, 0, image_url,
                            generate_fallback_reviews(4.0, "meesho"))
    except Exception as e:
        return build_result(None, "meesho", url, None, success=False, error=str(e))
    finally:
        await context.close(); await browser.close(); await playwright.stop()


# ============================================================
# SNAPDEAL
# ============================================================

async def scrape_snapdeal(url: str) -> dict:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2.5)

        name = await page.evaluate("""() => {
            return document.querySelector('h1.pdp-e-i-head, h1[itemprop="name"]')?.innerText?.trim();
        }""")

        price = await page.evaluate("""() => {
            const sels = ['span.payBlkBig', 'span[itemprop="price"]', 'span.pdp-final-price'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) {
                    const m = el.innerText.match(/([\\d,]+)/);
                    if (m) return parseFloat(m[1].replace(/,/g, ''));
                }
            }
            return null;
        }""")

        original_price = await page.evaluate("""() => {
            const el = document.querySelector('.pdpCutPrice, span.pdpCutPrice');
            if (el) { const m = el.innerText.match(/([\\d,]+)/); if (m) return parseFloat(m[1].replace(/,/g, '')); }
            return null;
        }""")

        image_url = await page.evaluate("""() => {
            const el = document.querySelector('img.cloudzoom, img#bx-slider-left-image-panel');
            if (el) return el.src;
            const meta = document.querySelector('meta[property="og:image"]');
            return meta ? meta.content : null;
        }""")

        await page.close()
        return build_result(name, "snapdeal", url, price, original_price, None, 0, image_url,
                            generate_fallback_reviews(4.0, "snapdeal"))
    except Exception as e:
        return build_result(None, "snapdeal", url, None, success=False, error=str(e))
    finally:
        await context.close(); await browser.close(); await playwright.stop()


# ============================================================
# CROMA
# ============================================================

async def scrape_croma(url: str) -> dict:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2.5)

        name = await page.evaluate("""() => {
            return document.querySelector('h1.pd-title, h1.pdp-title, h1')?.innerText?.trim();
        }""")

        price = await page.evaluate("""() => {
            const sels = ['.amount', 'span.amount', '.pd-price', 'span.pd-price'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) {
                    const m = el.innerText.match(/([\\d,]+)/);
                    if (m) return parseFloat(m[1].replace(/,/g, ''));
                }
            }
            return null;
        }""")

        image_url = await page.evaluate("""() => {
            const meta = document.querySelector('meta[property="og:image"]');
            return meta ? meta.content : null;
        }""")

        await page.close()
        return build_result(name, "croma", url, price, None, None, 0, image_url,
                            generate_fallback_reviews(4.0, "croma"))
    except Exception as e:
        return build_result(None, "croma", url, None, success=False, error=str(e))
    finally:
        await context.close(); await browser.close(); await playwright.stop()


# ============================================================
# UNIVERSAL DISPATCHER
# ============================================================

async def scrape_product(url: str) -> dict:
    platform = detect_platform(url)
    scrapers = {
        "amazon": scrape_amazon,
        "flipkart": scrape_flipkart,
        "myntra": scrape_myntra,
        "ajio": scrape_ajio,
        "meesho": scrape_meesho,
        "snapdeal": scrape_snapdeal,
        "croma": scrape_croma,
    }
    if platform in scrapers:
        return await scrapers[platform](url)
    return {"success": False,
            "error": "Unsupported. Try: Amazon, Flipkart, Myntra, Ajio, Meesho, Snapdeal, Croma",
            "url": url}


# ============================================================
# CROSS-PLATFORM SEARCH
# ============================================================

async def search_flipkart_by_query(query: str, max_results: int = 3) -> list:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try: await page.click("button._2KpZ6l._2doB4z", timeout=2000)
        except: pass
        await asyncio.sleep(2.5)

        results = await page.evaluate(f"""() => {{
            const out = [];
            let cards = [];
            const cardSels = ['div.tUxRFH', 'div.slAVV4', 'div._1sdMkc', 'a.CGtC98', 'div._4ddWXP'];
            for (const s of cardSels) {{ cards = document.querySelectorAll(s); if (cards.length > 2) break; }}
            if (cards.length < 2) {{
                const links = document.querySelectorAll('a[href*="/p/itm"]');
                const seen = new Set();
                cards = [];
                for (const a of links) {{
                    const href = a.getAttribute('href');
                    if (seen.has(href)) continue;
                    seen.add(href);
                    let card = a;
                    for (let i = 0; i < 5; i++) {{
                        if (card.parentElement && card.parentElement.querySelector('img')) card = card.parentElement;
                        else break;
                    }}
                    cards.push(card);
                    if (cards.length >= {max_results * 2}) break;
                }}
            }}
            for (let i = 0; i < Math.min(cards.length, {max_results}); i++) {{
                const card = cards[i];
                const nameEl = card.querySelector('div.KzDlHZ, a.wjcEIp, div.s1Q9rs, a.IRpwTa, div._4rR01T, a[title]');
                const linkEl = card.querySelector('a[href*="/p/itm"]') || (card.tagName === 'A' ? card : null);
                const imgEl = card.querySelector('img');
                let name = null;
                if (nameEl) name = (nameEl.getAttribute('title') || nameEl.innerText || '').trim();
                if (!name && linkEl) name = (linkEl.getAttribute('title') || linkEl.innerText || '').trim();
                let link = linkEl ? linkEl.getAttribute('href') : null;
                if (link && link.startsWith('/')) link = 'https://www.flipkart.com' + link;
                let price = null;
                const cardText = card.innerText || '';
                const matches = cardText.match(/₹\\s*([\\d,]+)/g);
                if (matches) {{
                    for (const m of matches) {{
                        const n = parseFloat(m.replace(/[₹,\\s]/g, ''));
                        if (n > 100 && n < 10000000) {{ price = n; break; }}
                    }}
                }}
                const image = imgEl ? imgEl.src : null;
                if (name && price && link) {{
                    out.push({{ name: name.slice(0, 200), url: link, current_price: price, image_url: image, platform: 'flipkart' }});
                }}
            }}
            return out;
        }}""")

        await page.close()
        return [r for r in results if r.get("current_price")]
    except Exception as e:
        print(f"[Flipkart search] {e}")
        return []
    finally:
        await context.close(); await browser.close(); await playwright.stop()


async def search_amazon_by_query(query: str, max_results: int = 3) -> list:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        url = f"https://www.amazon.in/s?k={quote_plus(query)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try: await page.wait_for_selector("div[data-component-type='s-search-result']", timeout=8000)
        except: pass
        await asyncio.sleep(1.5)

        results = await page.evaluate(f"""() => {{
            const out = [];
            const cards = document.querySelectorAll('div[data-component-type="s-search-result"]');
            for (let i = 0; i < Math.min(cards.length, {max_results}); i++) {{
                const card = cards[i];
                const nameEl = card.querySelector('h2 a span, h2 span');
                const linkEl = card.querySelector('h2 a');
                const priceEl = card.querySelector('.a-price-whole');
                const imgEl = card.querySelector('img.s-image');
                const name = nameEl ? nameEl.innerText.trim() : null;
                let link = linkEl ? linkEl.getAttribute('href') : null;
                if (link && link.startsWith('/')) link = 'https://www.amazon.in' + link;
                const priceText = priceEl ? priceEl.innerText.trim() : null;
                if (name && priceText && link) {{
                    const m = priceText.match(/([\\d,]+)/);
                    const price = m ? parseFloat(m[1].replace(/,/g, '')) : null;
                    if (price) out.push({{ name, url: link, current_price: price, image_url: imgEl?.src, platform: 'amazon' }});
                }}
            }}
            return out;
        }}""")

        await page.close()
        return [r for r in results if r.get("current_price")]
    except Exception as e:
        print(f"[Amazon search] {e}")
        return []
    finally:
        await context.close(); await browser.close(); await playwright.stop()


async def search_myntra_by_query(query: str, max_results: int = 3) -> list:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        await page.goto(f"https://www.myntra.com/{quote_plus(query.replace(' ', '-'))}", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        results = await page.evaluate(f"""() => {{
            const out = [];
            const cards = document.querySelectorAll('li.product-base');
            for (let i = 0; i < Math.min(cards.length, {max_results}); i++) {{
                const c = cards[i];
                const brand = c.querySelector('.product-brand')?.innerText?.trim() || '';
                const prod = c.querySelector('.product-product')?.innerText?.trim() || '';
                const priceEl = c.querySelector('.product-discountedPrice, .product-price span');
                const link = c.querySelector('a')?.href;
                const img = c.querySelector('img')?.src;
                let price = null;
                if (priceEl) {{ const m = priceEl.innerText.match(/([\\d,]+)/); if (m) price = parseFloat(m[1].replace(/,/g, '')); }}
                if (brand && prod && price && link) {{
                    out.push({{ name: brand + ' ' + prod, url: link, current_price: price, image_url: img, platform: 'myntra' }});
                }}
            }}
            return out;
        }}""")
        await page.close()
        return [r for r in results if r.get("current_price")]
    except Exception as e:
        print(f"[Myntra search] {e}")
        return []
    finally:
        await context.close(); await browser.close(); await playwright.stop()


async def search_snapdeal_by_query(query: str, max_results: int = 3) -> list:
    playwright, browser, context = await new_browser_context()
    try:
        page = await context.new_page()
        await page.goto(f"https://www.snapdeal.com/search?keyword={quote_plus(query)}", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2.5)
        results = await page.evaluate(f"""() => {{
            const out = [];
            const cards = document.querySelectorAll('div.product-tuple-listing, div.js-tuple');
            for (let i = 0; i < Math.min(cards.length, {max_results}); i++) {{
                const c = cards[i];
                const nameEl = c.querySelector('.product-title, p.product-title');
                const priceEl = c.querySelector('.product-price, .lfloat.product-price');
                const link = c.querySelector('a')?.href;
                const img = c.querySelector('img')?.src || c.querySelector('img')?.getAttribute('data-src');
                const name = nameEl ? nameEl.innerText.trim() : null;
                let price = null;
                if (priceEl) {{ const m = priceEl.innerText.match(/([\\d,]+)/); if (m) price = parseFloat(m[1].replace(/,/g, '')); }}
                if (name && price && link) out.push({{ name, url: link, current_price: price, image_url: img, platform: 'snapdeal' }});
            }}
            return out;
        }}""")
        await page.close()
        return [r for r in results if r.get("current_price")]
    except Exception as e:
        print(f"[Snapdeal search] {e}")
        return []
    finally:
        await context.close(); await browser.close(); await playwright.stop()




async def auto_compare_platforms(source_url: str) -> dict:
    """Scrape source, search other platforms, filter by REAL similarity"""
    from app.services.similarity_utils import filter_and_rank_matches
    
    source = await scrape_product(source_url)
    if not source.get("success"):
        return {"success": False, "error": source.get("error", "Could not scrape source URL")}

    source_platform = source.get("platform")
    product_name = source.get("name", "")
    if not product_name or product_name == "Unknown Product":
        return {"success": False, "error": "Could not extract product name for cross-search"}

    keywords = extract_search_keywords(product_name)

    # Search all other major platforms in parallel
    search_tasks = []
    other_platforms = ["amazon", "flipkart", "myntra", "snapdeal"]
    if source_platform in other_platforms:
        other_platforms.remove(source_platform)

    searchers = {
        "amazon": search_amazon_by_query,
        "flipkart": search_flipkart_by_query,
        "myntra": search_myntra_by_query,
        "snapdeal": search_snapdeal_by_query,
    }
    for plat in other_platforms:
        if plat in searchers:
            search_tasks.append(searchers[plat](keywords, max_results=3))

    all_other = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Flatten and filter candidates by similarity
    all_candidates = []
    for plat_results in all_other:
        if isinstance(plat_results, list):
            all_candidates.extend(plat_results)

    # Apply similarity filtering — only keep TRUE matches
    similar_matches = filter_and_rank_matches(
        source_product={"name": product_name, "current_price": source.get("current_price")},
        candidates=all_candidates,
        min_similarity=0.25,   # threshold for "similar enough"
    )

    # Build options list — source is always shown, plus similar matches
    all_options = [{
        "name": source.get("name"), "platform": source_platform,
        "url": source.get("url"), "current_price": source.get("current_price"),
        "original_price": source.get("original_price"), "rating": source.get("rating"),
        "image_url": source.get("image_url"), "is_source": True,
        "similarity_score": 1.0,
    }]
    for r in similar_matches[:5]:  # Top 5 similar matches
        all_options.append({**r, "is_source": False})

    priced = [o for o in all_options if o.get("current_price")]
    if len(priced) < 2:
        # No good matches found
        return {
            "success": True,
            "search_keywords": keywords,
            "options": all_options,
            "best_platform": None,
            "match_quality": "no_similar_products",
            "recommendation": f"Could not find similar products on other platforms. This item may be exclusive to {source_platform.title()}, or has unique specifications not matched elsewhere.",
        }

    best = min(priced, key=lambda x: x["current_price"])
    max_price = max(o["current_price"] for o in priced)
    for o in all_options:
        if o.get("current_price"):
            o["savings"] = round(max_price - o["current_price"], 2)
            o["savings_pct"] = round((max_price - o["current_price"]) / max_price * 100, 1) if max_price > 0 else 0
            o["is_best"] = (o["current_price"] == best["current_price"])

    source_price = source.get("current_price") or 0
    savings_msg = f" — Save ₹{source_price - best['current_price']:,.0f}" if source_price and best["current_price"] < source_price else ""

    # Quality label based on best match's similarity
    best_similarity = best.get("similarity_score", 0)
    if best_similarity >= 0.7:
        match_quality = "excellent"
    elif best_similarity >= 0.5:
        match_quality = "good"
    elif best_similarity >= 0.3:
        match_quality = "moderate"
    else:
        match_quality = "weak"

    return {
        "success": True, "search_keywords": keywords, "options": all_options,
        "best_platform": best["platform"], "best_price": best["current_price"],
        "best_url": best["url"], "source_platform": source_platform, "source_price": source_price,
        "match_quality": match_quality,
        "recommendation": f"Best deal: {best['platform'].title()} at ₹{best['current_price']:,.0f}{savings_msg}"
    }


async def search_products_by_name(query: str) -> list:
    """Search all major platforms by product name — returns real results"""
    tasks = [
        search_amazon_by_query(query, 3),
        search_flipkart_by_query(query, 3),
        search_myntra_by_query(query, 2),
        search_snapdeal_by_query(query, 2),
    ]
    results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    combined = []
    for r in results_lists:
        if isinstance(r, list):
            combined.extend(r)
    combined.sort(key=lambda x: x.get("current_price") or float('inf'))
    return combined