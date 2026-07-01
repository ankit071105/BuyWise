from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import auth, products, agents, chat, alerts, history
from app.database import engine, Base
from app.scheduler import start_scheduler, stop_scheduler, get_active_festival, get_upcoming_festival

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        start_scheduler()
    except Exception as e:
        print(f"[Warning] Scheduler failed to start: {e}")
    yield
    # Shutdown
    try:
        stop_scheduler()
    except:
        pass


app = FastAPI(
    title="BuyWise API",
    description="AI-powered smart shopping assistant backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(history.router, prefix="/api/history", tags=["history"])


@app.get("/")
def root():
    return {"message": "BuyWise API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/festival/status")
def festival_status():
    """Public endpoint — returns current active festival + upcoming one"""
    active = get_active_festival()
    upcoming = get_upcoming_festival(days_ahead=30)
    return {
        "active_festival": active,
        "upcoming_festival": upcoming,
        "is_sale_season": bool(active),
    }