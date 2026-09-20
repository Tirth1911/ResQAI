from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.websocket.manager import ws_manager

router = APIRouter()


class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str = "HIGH"  # LOW, MEDIUM, HIGH, CRITICAL
    target_area: Optional[str] = None
    affected_incident_id: Optional[str] = None


class AlertResponse(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    message: str
    severity: str
    target_area: Optional[str] = None
    affected_incident_id: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED, summary="Broadcast Emergency Alert")
async def create_alert(
    alert_in: AlertCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create and broadcast an emergency alert to all active clients."""
    doc = alert_in.model_dump()
    doc["created_at"] = datetime.utcnow()
    res = await db.alerts.insert_one(doc)
    doc["_id"] = str(res.inserted_id)

    # Also log to notifications collection
    notif_doc = {
        "notification_id": f"NOTIF-{str(res.inserted_id)[-6:].upper()}",
        "title": doc["title"],
        "message": doc["message"],
        "severity": doc.get("severity", "HIGH"),
        "created_at": doc["created_at"],
        "read": False
    }
    await db.notifications.insert_one(notif_doc)

    from backend.app.websocket.manager import WebSocketEventType
    await ws_manager.broadcast_event(WebSocketEventType.NOTIFICATION_CREATED, doc)
    return doc


@router.get("", response_model=List[AlertResponse], summary="List Emergency Alerts", include_in_schema=False)
@router.get("/", response_model=List[AlertResponse], summary="List Emergency Alerts")
async def list_alerts(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    cursor = db.alerts.find().sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results
