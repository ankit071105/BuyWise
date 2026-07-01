from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import SearchHistory, User
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/")
def get_search_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).order_by(SearchHistory.searched_at.desc()).limit(limit).all()
    return [
        {"id": h.id, "query": h.query, "product_id": h.product_id, "searched_at": h.searched_at.isoformat()}
        for h in history
    ]

@router.delete("/")
def clear_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Search history cleared"}
