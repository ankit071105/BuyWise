#!/bin/bash
# ⚡ BuyWise — Quick Start Script
# Run from the project root: bash quickstart.sh

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║   ⚡  BuyWise — Smart Shopping AI     ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not found. Install from python.org"; exit 1; }
command -v node    >/dev/null 2>&1 || { echo "❌ Node.js not found. Install from nodejs.org";  exit 1; }
command -v psql    >/dev/null 2>&1 || { echo "⚠️  PostgreSQL not found — make sure it's running"; }

echo "✅ Prerequisites OK"
echo ""

# Backend setup
echo "━━━ Setting up Backend ━━━"
cd backend

if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "✅ Created virtual environment"
fi
source venv/bin/activate

pip install -r requirements.txt -q
echo "✅ Backend dependencies installed"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  ACTION REQUIRED: Edit backend/.env and set:"
  echo "   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/buywise"
  echo "   GROQ_API_KEY=your_key_from_console.groq.com"
  echo "   SECRET_KEY=any_random_strong_string"
  echo ""
  read -p "Press Enter once you've edited .env to continue..."
fi

echo "✅ Backend .env ready"

# Frontend setup
echo ""
echo "━━━ Setting up Frontend ━━━"
cd ../frontend
npm install --silent
echo "✅ Frontend dependencies installed"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  🚀  Start the servers in separate terminals:    ║"
echo "║                                                  ║"
echo "║  Terminal 1 (Backend):                           ║"
echo "║    cd backend && source venv/bin/activate        ║"
echo "║    uvicorn app.main:app --reload --port 8000     ║"
echo "║                                                  ║"
echo "║  Terminal 2 (Frontend):                          ║"
echo "║    cd frontend && npm run dev                    ║"
echo "║                                                  ║"
echo "║  Then open: http://localhost:3000                ║"
echo "║  API docs:  http://localhost:8000/docs           ║"
echo "║                                                  ║"
echo "║  Extension: Load /extension folder in           ║"
echo "║             chrome://extensions (unpacked)       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
