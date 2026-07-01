from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models.models import ChatHistory, User
from app.api.auth import get_current_user
from app.agents.chat_agent import get_chat_response

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/message")
def send_message(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to BuyWise chat assistant"""
    # Load last 10 chat turns for context
    history_records = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).order_by(ChatHistory.created_at.desc()).limit(10).all()

    history = []
    for h in reversed(history_records):
        history.append({"role": "user", "content": h.message})
        history.append({"role": "assistant", "content": h.response})

    response = get_chat_response(req.message, history)

    # Save to DB
    chat = ChatHistory(
        user_id=current_user.id,
        message=req.message,
        response=response
    )
    db.add(chat)
    db.commit()

    return {"response": response, "message": req.message}


@router.get("/history")
def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's chat history"""
    chats = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).order_by(ChatHistory.created_at.desc()).limit(limit).all()

    return [
        {
            "id": c.id,
            "message": c.message,
            "response": c.response,
            "created_at": c.created_at.isoformat()
        }
        for c in reversed(chats)
    ]


@router.delete("/history")
def clear_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear user's chat history"""
    db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Chat history cleared"}
