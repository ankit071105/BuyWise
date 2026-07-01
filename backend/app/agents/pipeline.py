"""
BuyWise LangGraph Agent Pipeline
=================================
Agents:
  1. ProductResolverAgent  - resolves URL/name to product data + DEEP reviews
  2. PriceAnalystAgent     - analyses price history & prediction
  3. ReviewAnalystAgent    - sentiment, fake detection, fit signals
  4. SynthesisAgent        - computes Buy Score + LLM reasoning + Smart Features
"""

import os
import json
import asyncio
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from app.services.scraper import scrape_product, search_products_by_name
from app.services.review_scraper import fetch_amazon_reviews_deep
from app.services.review_analyzer import analyze_reviews, get_review_summary
from app.services.smart_features import compute_all_smart_features
from app.ml.predictor import predict_price_trend, compute_buy_score
from app.scheduler import get_active_festival, get_upcoming_festival

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def get_llm():
    if GROQ_API_KEY:
        return ChatGroq(
            api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )
    raise ValueError("No LLM API key found. Set GROQ_API_KEY in .env")


class AgentState(TypedDict):
    input_url: Optional[str]
    input_query: Optional[str]
    price_history: List[dict]
    product_data: Optional[dict]
    error: Optional[str]
    price_prediction: Optional[dict]
    reviewed_reviews: Optional[List[dict]]
    review_summary: Optional[dict]
    buy_score_data: Optional[dict]
    llm_reasoning: Optional[str]
    final_output: Optional[dict]


def _run_async(coro):
    """Safely run async code from sync context"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coro)
        loop.close()
        return result
    except Exception as e:
        print(f"[_run_async error] {e}")
        return None


def product_resolver_agent(state: AgentState) -> AgentState:
    """Node 1: Scrape URL + fetch deep reviews for Amazon"""
    try:
        if state.get("input_url"):
            result = _run_async(scrape_product(state["input_url"]))
            if result and result.get("success"):
                state["product_data"] = result

                # DEEP REVIEW SCRAPE for Amazon products
                if result.get("platform") == "amazon":
                    print("[Pipeline] Fetching deep Amazon reviews...")
                    deep_reviews = _run_async(fetch_amazon_reviews_deep(state["input_url"], max_reviews=15))
                    if deep_reviews and len(deep_reviews) > 0:
                        result["reviews"] = deep_reviews
                        print(f"[Pipeline] Got {len(deep_reviews)} real reviews")
            else:
                state["error"] = (result or {}).get("error", "Scraping failed")
        elif state.get("input_query"):
            results = _run_async(search_products_by_name(state["input_query"]))
            if results:
                state["product_data"] = results[0]
                state["product_data"]["success"] = True
            else:
                state["error"] = "No products found"
        else:
            state["error"] = "No URL or query provided"
    except Exception as e:
        state["error"] = f"Resolver error: {str(e)}"
    return state


def price_analyst_agent(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    price_history = state.get("price_history", [])
    product_data = state.get("product_data", {})
    if product_data.get("current_price") and not price_history:
        from datetime import datetime
        price_history = [{"price": product_data["current_price"], "scraped_at": datetime.utcnow().isoformat()}]
    state["price_prediction"] = predict_price_trend(price_history, days_ahead=30)
    return state


def review_analyst_agent(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    raw_reviews = state.get("product_data", {}).get("reviews", [])
    if not raw_reviews:
        state["reviewed_reviews"] = []
        state["review_summary"] = {"total": 0, "fake_count": 0, "avg_sentiment": 0, "fit_summary": {}}
        return state
    analyzed = analyze_reviews(raw_reviews)
    summary = get_review_summary(analyzed)
    state["reviewed_reviews"] = analyzed
    state["review_summary"] = summary
    return state


def synthesis_agent(state: AgentState) -> AgentState:
    if state.get("error"):
        state["final_output"] = {"success": False, "error": state["error"]}
        return state

    product = state.get("product_data", {})
    price_records = state.get("price_history", [])
    reviews = state.get("reviewed_reviews", [])
    prediction = state.get("price_prediction", {})
    review_summary = state.get("review_summary", {})

    current_price = product.get("current_price", 0) or 0

    # Festival context
    active_festival = get_active_festival()
    upcoming_festival = get_upcoming_festival(days_ahead=15)
    festival_context = ""
    if active_festival:
        festival_context = f"ACTIVE NOW: {active_festival['name']}"
    elif upcoming_festival:
        festival_context = f"UPCOMING: {upcoming_festival['name']} in {upcoming_festival['days_away']} days"

    score_data = compute_buy_score(current_price, price_records, reviews, prediction)

    # Warm Hinglish LLM reasoning
    llm_reasoning = ""
    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are BuyWise AI Assistant, a warm Indian shopping guide.

Personality: Conversational Hinglish tone with natural words like acha, bilkul, sahi, haan.
Never robotic. Never generic.

Write a 3-4 sentence buying recommendation using ONLY the real data provided.
Structure:
1. Warm opener acknowledging the product
2. State the Buy Score with clear verdict
3. Mention specific insight (real price, review count, fake reviews, fit signal, or festival)
4. End with actionable suggestion

Do NOT use bullet points. Write flowing conversation. Never invent numbers."""),
            ("human", """Product Name: {name}
Platform: {platform}
Current Price (rupees): {price}
Historical Min: {hist_min}
Price Trend: {trend}
Buy Score: {score}/10
Recommendation: {recommendation}
Genuine Reviews: {genuine}
Fake Reviews Detected: {fake_count}
Review Sentiment: {sentiment}
Fit Signal (for shoes): {fit_signal}
Festival Context: {festival}

Give your friendly Hinglish recommendation:""")
        ])
        chain = prompt | llm
        response = chain.invoke({
            "name": product.get("name", "This product"),
            "platform": product.get("platform", "unknown"),
            "price": current_price,
            "hist_min": prediction.get("historical_min", "N/A"),
            "trend": prediction.get("trend", "unknown"),
            "score": score_data["score"],
            "recommendation": score_data.get("recommendation_label", ""),
            "genuine": review_summary.get("valid_count", 0),
            "fake_count": review_summary.get("fake_count", 0),
            "sentiment": review_summary.get("sentiment_label", "N/A"),
            "fit_signal": review_summary.get("dominant_fit", "not detected"),
            "festival": festival_context or "no active sale",
        })
        llm_reasoning = response.content
    except Exception as e:
        llm_reasoning = score_data.get("reasoning", f"Analysis complete. {str(e)[:100]}")

    state["buy_score_data"] = score_data
    state["llm_reasoning"] = llm_reasoning

    # Run smart features (Price Manipulation, Regret, TCO, Sustainability, Alternatives)
    print("[Pipeline] Running smart features...")
    smart_features = _run_async(compute_all_smart_features(
        product_data=product,
        buy_score_data=score_data,
        price_history=price_records,
        reviews=reviews,
    ))
    if smart_features:
        print("[Pipeline] Smart features computed")

    state["final_output"] = {
        "success": True,
        "product": product,
        "buy_score": score_data,
        "price_prediction": prediction,
        "review_summary": review_summary,
        "llm_reasoning": llm_reasoning,
        "price_history": price_records,
        "festival": {
            "active": active_festival,
            "upcoming": upcoming_festival,
        },
        "smart_features": smart_features or {},
    }
    return state


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("resolver", product_resolver_agent)
    graph.add_node("price_analyst", price_analyst_agent)
    graph.add_node("review_analyst", review_analyst_agent)
    graph.add_node("synthesis", synthesis_agent)
    graph.set_entry_point("resolver")
    graph.add_edge("resolver", "price_analyst")
    graph.add_edge("price_analyst", "review_analyst")
    graph.add_edge("review_analyst", "synthesis")
    graph.add_edge("synthesis", END)
    return graph.compile()


buywise_pipeline = build_agent_graph()


def run_pipeline(url: str = None, query: str = None, price_history: list = None) -> dict:
    result = buywise_pipeline.invoke({
        "input_url": url,
        "input_query": query,
        "price_history": price_history or [],
        "product_data": None,
        "error": None,
        "price_prediction": None,
        "reviewed_reviews": None,
        "review_summary": None,
        "buy_score_data": None,
        "llm_reasoning": None,
        "final_output": None,
    })
    return result.get("final_output", {"success": False, "error": "Pipeline failed"})