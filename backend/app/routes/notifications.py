from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from backend.app.database import get_database
from backend.app.services.db_service import clean_mongo_docs, clean_mongo_doc
from backend.app.services.alert_service import AlertService, AlertSeverity, AlertType
from backend.app.websocket.manager import ws_manager, WebSocketEventType

router = APIRouter()


@router.get("", summary="List In-App Notifications & Alerts", include_in_schema=False)
@router.get("/", summary="List In-App Notifications & Alerts")
async def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, CRITICAL)"),
    alert_type: Optional[str] = Query(None, alias="type", description="Filter by alert type"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Retrieve notifications and alerts with filtering and descending sort by created_at."""
    query: Dict[str, Any] = {}
    if unread_only:
        query["read"] = False
    if severity:
        query["severity"] = severity.upper()
    if alert_type:
        query["type"] = alert_type

    cursor = db.notifications.find(query).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return clean_mongo_docs(docs)


@router.patch("/{id}/read", summary="Mark Notification as Read")
async def mark_notification_as_read(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Mark a specific notification as read by alert_id, notification_id, or ObjectId."""
    query: Dict[str, Any] = {"$or": [{"alert_id": id}, {"notification_id": id}]}
    if ObjectId.is_valid(id):
        query["$or"].append({"_id": ObjectId(id)})

    result = await db.notifications.update_one(
        query,
        {"$set": {"read": True}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with identifier '{id}' not found."
        )

    updated = await db.notifications.find_one(query)
    cleaned = clean_mongo_doc(updated)

    await ws_manager.broadcast_event("NOTIFICATION_UPDATED", cleaned)
    return cleaned


@router.post("/mark-all-read", summary="Mark All Notifications as Read")
async def mark_all_notifications_as_read(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Mark all unread notifications in MongoDB as read."""
    result = await db.notifications.update_many(
        {"read": False},
        {"$set": {"read": True}}
    )

    await ws_manager.broadcast_event("NOTIFICATIONS_ALL_READ", {"modified_count": result.modified_count})

    return {
        "status": "success",
        "marked_read_count": result.modified_count
    }


@router.delete("/{id}", summary="Delete Notification")
async def delete_notification(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a notification by alert_id or ObjectId."""
    query: Dict[str, Any] = {"$or": [{"alert_id": id}, {"notification_id": id}]}
    if ObjectId.is_valid(id):
        query["$or"].append({"_id": ObjectId(id)})

    result = await db.notifications.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{id}' not found."
        )

    return {"status": "deleted", "id": id}
