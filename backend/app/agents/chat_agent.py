"""
BuyWise Chat Agent — Tool-using LangChain agent
"""
import os
import asyncio
import json
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from app.agents.pipeline import run_pipeline
from app.services.scraper import auto_compare_platforms

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


@tool
def analyze_product(url: str) -> str:
    """
    Analyze a product from an Amazon.in, Flipkart, Myntra, Ajio, Meesho, Snapdeal, or Croma URL.
    Returns real Buy Score (0-10), current price, review analysis, and price prediction.
    Call this whenever the user pastes a product URL or asks about a specific product.
    """
    try:
        result = run_pipeline(url=url, price_history=[])
        if not result.get("success"):
            return f"ANALYSIS_FAILED: {result.get('error', 'Unknown error')}"

        product = result.get("product", {})
        score = result.get("buy_score", {})
        review_summary = result.get("review_summary", {})

        return json.dumps({
            "product_name": product.get("name"),
            "platform": product.get("platform"),
            "current_price": product.get("current_price"),
            "original_price": product.get("original_price"),
            "rating": product.get("rating"),
            "review_count": product.get("review_count"),
            "buy_score": score.get("score"),
            "recommendation": score.get("recommendation_label"),
            "price_score": score.get("price_score"),
            "review_score": score.get("review_score"),
            "timing_score": score.get("timing_score"),
            "predicted_low_price": score.get("predicted_low_price"),
            "predicted_low_days": score.get("predicted_low_days"),
            "trend": score.get("trend"),
            "fake_review_count": score.get("fake_review_count"),
            "genuine_reviews": review_summary.get("valid_count"),
            "sentiment": review_summary.get("sentiment_label"),
            "fit_signal": review_summary.get("dominant_fit"),
            "reasoning": result.get("llm_reasoning"),
        }, indent=2)
    except Exception as e:
        return f"ANALYSIS_FAILED: {str(e)}"


@tool
def compare_prices_across_platforms(url: str) -> str:
    """
    Given a product URL from ANY platform, automatically scrape it and search all
    OTHER platforms (Amazon, Flipkart, Myntra, Snapdeal) for the same product.
    Returns real prices from multiple e-commerce sites side by side.
    Use this when user asks for cheaper alternatives or wants to compare platforms.
    """
    try:
        result = asyncio.run(auto_compare_platforms(url))
        if not result.get("success"):
            return f"COMPARE_FAILED: {result.get('error')}"

        options = result.get("options", [])
        formatted = []
        for o in options:
            if o.get("current_price"):
                formatted.append({
                    "platform": o.get("platform"),
                    "name": o.get("name"),
                    "price": o.get("current_price"),
                    "original_price": o.get("original_price"),
                    "rating": o.get("rating"),
                    "url": o.get("url"),
                    "is_source": o.get("is_source", False),
                    "is_best": o.get("is_best", False),
                    "savings": o.get("savings"),
                })

        return json.dumps({
            "best_platform": result.get("best_platform"),
            "best_price": result.get("best_price"),
            "source_platform": result.get("source_platform"),
            "options": formatted,
            "recommendation": result.get("recommendation"),
        }, indent=2)
    except Exception as e:
        return f"COMPARE_FAILED: {str(e)}"


@tool
def get_buywise_info(topic: str) -> str:
    """
    Get information about BuyWise features. Use for how-to questions.
    Valid topics: buy_score, fake_reviews, fit_signal, alerts, tracking, general.
    """
    info = {
        "buy_score": "Buy Score (0-10) combines Price Position (40%), Review Quality (35%), and Buy Timing (25%). Score 7.5+ Great Buy, 5.5-7.4 Consider, 4.0-5.4 Wait, below 4.0 Avoid.",
        "fake_reviews": "BuyWise detects fake reviews via burst-pattern detection, rating-text mismatch, and generic template language patterns. Suspicious reviews are excluded from the Buy Score.",
        "fit_signal": "For shoes, BuyWise mines review text for size mentions like runs small, runs large, true to size. Helps reduce returns.",
        "alerts": "Set price drop alerts on any tracked product with a target price. Get notified via email, browser, or Telegram.",
        "tracking": "Click Track This on any analyzed product. It appears in your Dashboard tracked list, re-scraped every few hours.",
        "general": "BuyWise is an AI-powered smart shopping assistant for Indian e-commerce. Paste any product URL from Amazon, Flipkart, Myntra, Ajio, Meesho, Snapdeal, or Croma to get real Buy Score, price prediction, fake review detection, and cross-platform comparison.",
    }
    return info.get(topic, info["general"])


# System prompt — no curly-brace variables inside the example text
SYSTEM_PROMPT = """You are BuyWise AI Assistant — a friendly Indian shopping guide.

Personality:
- Warm, conversational Hinglish tone (mix English with words like acha, bilkul, sahi, namaste, haan)
- Concise: 2-4 sentences per response max
- Use rupee symbol for prices
- Never make up numbers, prices, scores, or facts

CRITICAL RULES:
1. When user pastes a product URL, ALWAYS call the analyze_product tool first
2. When user asks cheaper elsewhere or compare platforms, call compare_prices_across_platforms
3. When user asks how BuyWise works, call get_buywise_info with appropriate topic
4. NEVER invent Buy Scores, prices, ratings, or historical data. Only use data returned by tools.
5. If a tool returns ANALYSIS_FAILED or COMPARE_FAILED, tell the user honestly and suggest they verify the URL

When you get tool results:
- Format the real numbers naturally in Hinglish
- Always mention the Buy Score and recommendation
- Use the reasoning field from the tool as your response basis when available
- Suggest a next step: track it, set alert, or compare platforms
- Do not use bullet points, write in flowing conversation

If a user asks a general shopping question without a URL, answer briefly and suggest they paste a product URL for real analysis."""


def get_agent_executor():
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )
    tools = [analyze_product, compare_prices_across_platforms, get_buywise_info]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=4, handle_parsing_errors=True)


def get_chat_response(message: str, history: list = None) -> str:
    if not GROQ_API_KEY:
        return "Chat agent not configured. Add GROQ_API_KEY to backend .env"

    try:
        executor = get_agent_executor()
        chat_history = []
        if history:
            for h in history[-6:]:
                if h["role"] == "user":
                    chat_history.append(HumanMessage(content=h["content"]))
                elif h["role"] == "assistant":
                    chat_history.append(AIMessage(content=h["content"]))

        result = executor.invoke({
            "input": message,
            "chat_history": chat_history,
        })
        return result.get("output", "Sorry, I could not process that.")
    except Exception as e:
        return f"Sorry, there was an error: {str(e)}. Please try again."