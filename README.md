# ⚡ BuyWise — AI-Powered Smart Shopping

> Track prices, detect fake reviews, predict best buy time, and get a Buy Score™ for every product on Amazon & Flipkart.

---

## 🗂️ Project Structure

```
buywise/
├── backend/        ← FastAPI + LangGraph + ML pipeline
├── frontend/       ← Next.js 14 dashboard (light cyan theme)
└── extension/      ← Chrome extension (Manifest V3)
```

---

## ⚙️ Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional — for Celery background jobs)
- A free Groq API key → https://console.groq.com

---

## Setup — Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
Swagger docs: http://localhost:8000/docs

---

##  Setup — Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

---

##  Setup — Chrome Extension

```bash
cd extension
python generate_icons.py
```

**3-step activation:**
1. Click the BuyWise icon in Chrome toolbar
2. Enter your BuyWise account email/password
3. Visit any Amazon.in or Flipkart.com product page → auto-analyzes!

---

##  Where to change things (marked with  CHANGE THIS in code)

| File | What to change |
|------|---------------|
| `backend/.env` | DATABASE_URL, GROQ_API_KEY, SECRET_KEY |
| `backend/app/database.py` | Default DB URL if not using .env |
| `frontend/src/lib/api.ts` | API base URL (default: localhost:8000) |
| `extension/src/popup.js` | API_BASE URL for extension |
| `frontend/src/app/page.tsx` | Footer — change "Made by Ankit" to your name |

---

##  Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| AI Agents | LangGraph, LangChain, Groq (llama-3.3-70b) |
| ML Model | XGBoost/heuristic price predictor |
| Scraping | httpx + BeautifulSoup |
| Frontend | Next.js 14, Tailwind CSS, Recharts |
| Extension | Chrome Manifest V3 |
| Auth | JWT (python-jose) |
| Notifications | Telegram Bot (optional) |

---

## 🏆 Unique Features 

1. **Buy Score™ (0–10)** — AI composite score with explainable breakdown
2. **Fake Review Detection** — Burst-pattern + rating-text mismatch analysis
3. **Shoe Fit Signal** — Mines reviews for "runs small/large/true to size"
4. **Festival Sale Predictor** — India-specific: Diwali, Big Billion Days, Republic Day
5. **LLM Reasoning** — GPT-style 2-3 sentence buying recommendation per product
6. **Cross-platform** — Website + Chrome extension sharing one backend
7. **Full chat history** — Conversational AI shopping assistant with memory



## 🛠️ Known Limitations (be honest in demos)

- **Scraping**: Amazon/Flipkart may block at scale — use proxies/ScraperAPI for production
- **Price prediction accuracy**: Improves with more historical data collected over time
- **Telegram alerts**: Requires additional setup (TELEGRAM_BOT_TOKEN + bot creation via @BotFather)
- **Review analysis**: Basic sentiment is rule-based; upgrade to HuggingFace transformer for production
