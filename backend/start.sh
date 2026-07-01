#!/bin/bash
# ⚡ BuyWise Backend Startup Script
# Run this from the /backend directory

echo "🔧 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || python -m venv venv && source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

echo "✅ Checking .env..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  Created .env from template — please add your GROQ_API_KEY and DATABASE_URL"
  exit 1
fi

echo "🚀 Starting BuyWise API server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
