from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import Alert, SearchHistory, User
from app.api.auth import get_current_user

router = APIRouter()


class AlertRequest(BaseModel):
    product_id: int
    alert_type: str  # "price_drop", "buy_score", "festival"
    threshold: Optional[float] = None
    channel: str = "email"  # "email", "telegram", "browser"


@router.post("/")
def create_alert(req: AlertRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = Alert(
        user_id=current_user.id,
        product_id=req.product_id,
        alert_type=req.alert_type,
        threshold=req.threshold,
        channel=req.channel
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {"message": "Alert created", "alert_id": alert.id}


@router.get("/")
def get_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alerts = db.query(Alert).filter(Alert.user_id == current_user.id, Alert.is_active == True).all()
    return [{"id": a.id, "product_id": a.product_id, "alert_type": a.alert_type,
             "threshold": a.threshold, "channel": a.channel, "is_triggered": a.is_triggered} for a in alerts]


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if alert:
        alert.is_active = False
        db.commit()
    return {"message": "Alert removed"}
