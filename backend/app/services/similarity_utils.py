"""
Product similarity scorer — no ML, just smart text + price heuristics.
Used to filter cross-platform search results to only show REAL matches.
"""
import re
from typing import Optional

def normalize_text(text: str) -> str:
    """Lowercase, remove special chars, collapse whitespace"""
    if not text:
        return ""
    t = re.sub(r'[^\w\s]', ' ', text.lower())
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def extract_key_tokens(product_name: str) -> set:
    """Extract meaningful tokens (brand, model, style code) from product name"""
    if not product_name:
        return set()

    STOPWORDS = {
        "for", "with", "and", "the", "of", "in", "at", "by", "to", "on",
        "men", "women", "kids", "boys", "girls", "unisex", "male", "female",
        "size", "small", "medium", "large", "xl", "xxl", "xxxl",
        "pack", "piece", "set", "packet", "packs",
        "new", "latest", "premium", "genuine", "original", "quality",
        "color", "colors", "colour", "colours", "multi",
        "cotton", "polyester", "fabric", "material",  # too generic in category
    }

    normalized = normalize_text(product_name)
    tokens = set(normalized.split()) - STOPWORDS
    # Keep only meaningful tokens (length > 2)
    return {t for t in tokens if len(t) > 2}


def compute_similarity(source_name: str, candidate_name: str,
                        source_price: Optional[float] = None,
                        candidate_price: Optional[float] = None) -> float:
    """
    Score how similar two products are (0-1).
    - Uses Jaccard similarity of key tokens (60%)
    - Uses price proximity (40%)
    """
    if not source_name or not candidate_name:
        return 0.0

    src_tokens = extract_key_tokens(source_name)
    cand_tokens = extract_key_tokens(candidate_name)

    # Jaccard similarity
    if not src_tokens or not cand_tokens:
        text_score = 0.0
    else:
        intersection = src_tokens & cand_tokens
        union = src_tokens | cand_tokens
        text_score = len(intersection) / len(union) if union else 0

        # Bonus for brand match — first significant token
        first_src = sorted(src_tokens)[0] if src_tokens else ""
        if first_src and first_src in cand_tokens:
            text_score = min(1.0, text_score + 0.15)

    # Price proximity score
    price_score = 0.5  # neutral if no prices
    if source_price and candidate_price and source_price > 0:
        ratio = min(source_price, candidate_price) / max(source_price, candidate_price)
        if ratio >= 0.75:
            price_score = 1.0
        elif ratio >= 0.5:
            price_score = 0.7
        elif ratio >= 0.3:
            price_score = 0.4
        else:
            price_score = 0.1

    return round(text_score * 0.6 + price_score * 0.4, 3)


def filter_and_rank_matches(source_product: dict, candidates: list,
                              min_similarity: float = 0.3) -> list:
    """
    Given source product and candidate list, return only similar matches
    sorted by similarity score.
    """
    source_name = source_product.get("name", "")
    source_price = source_product.get("current_price")

    scored = []
    for c in candidates:
        sim = compute_similarity(
            source_name,
            c.get("name", ""),
            source_price,
            c.get("current_price"),
        )
        if sim >= min_similarity:
            c_copy = {**c, "similarity_score": sim}
            scored.append(c_copy)

    # Sort by similarity descending
    scored.sort(key=lambda x: -x["similarity_score"])
    return scored
