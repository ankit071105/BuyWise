from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.api.auth import get_current_user
from app.models.models import User
from app.agents.pipeline import run_pipeline

router = APIRouter()

class QuickAnalyzeRequest(BaseModel):
    url: Optional[str] = None
    query: Optional[str] = None

@router.post("/analyze")
def quick_analyze(req: QuickAnalyzeRequest, current_user: User = Depends(get_current_user)):
    """Quick agent analysis without saving to DB — used by Chrome extension"""
    result = run_pipeline(url=req.url, query=req.query)
    return result
