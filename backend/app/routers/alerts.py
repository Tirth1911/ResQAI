from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.db import db
from backend.app.config import settings
from backend.app.services.alerts import evaluate_delayed_and_escalation_checks

router = APIRouter()


def format_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return {}
    res = dict(doc)
    if "_id" in res:
        res["id"] = str(res["_id"])
        res["_id"] = str(res["_id"])
    return res


# -----------------------------------------------------------------------------
# 1. GET /api/alerts - List Alerts (Filter Acknowledged)
# -----------------------------------------------------------------------------
@router.get(
    "/alerts",
    summary="Get List of Emergency Alerts",
    description="Retrieve emergency alerts with optional filtering by acknowledged state."
)
async def get_alerts(
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    limit: int = Query(100, ge=1, le=200)
):
    query: Dict[str, Any] = {}
    if acknowledged is not None:
        query["acknowledged"] = acknowledged

    cursor = db.alerts.find(query).sort([("created_at", -1)]).limit(limit)
    raw_alerts = await cursor.to_list(length=limit)
    return [format_doc(a) for a in raw_alerts]


# -----------------------------------------------------------------------------
# 2. POST /api/alerts/{id}/ack - Acknowledge Alert
# -----------------------------------------------------------------------------
@router.post(
    "/alerts/{id}/ack",
    summary="Acknowledge Alert",
    description="Mark an emergency alert as acknowledged."
)
async def acknowledge_alert(id: str):
    query = {"$or": [{"_id": ObjectId(id) if ObjectId.is_valid(id) else id}, {"alert_id": id}]}
    alert = await db.alerts.find_one(query)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    now_dt = datetime.now(timezone.utc)
    await db.alerts.update_one(
        {"_id": alert["_id"]},
        {"$set": {"acknowledged": True, "acknowledged_at": now_dt}}
    )

    updated = await db.alerts.find_one({"_id": alert["_id"]})
    return format_doc(updated)


# -----------------------------------------------------------------------------
# 3. GET /api/notifications - List Latest Notifications
# -----------------------------------------------------------------------------
@router.get(
    "/notifications",
    summary="Get Latest Notifications",
    description="Retrieve latest 100 in-app / multi-channel notification logs."
)
async def get_notifications(limit: int = Query(100, ge=1, le=200)):
    cursor = db.notifications.find({}).sort([("created_at", -1)]).limit(limit)
    logs = await cursor.to_list(length=limit)
    return [format_doc(n) for n in logs]


# -----------------------------------------------------------------------------
# 4. POST /api/dev/tick - Execute Immediate Escalation & Delayed Checks (Demo Mode)
# -----------------------------------------------------------------------------
@router.post(
    "/dev/tick",
    summary="Trigger Escalation & Delayed Response Monitor",
    description="Forces immediate run of delayed response and escalation background checks."
)
async def dev_tick_trigger(
    time_scale: float = Query(1.0, description="Demo time scale acceleration factor")
):
    count = await evaluate_delayed_and_escalation_checks(db.db, demo_time_scale=time_scale)
    return {
        "status": "executed",
        "alerts_generated": count,
        "time_scale": time_scale,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
