import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from backend.app.services.notify import NotificationService
from backend.app.websocket.manager import ws_manager, WebSocketEventType

logger = logging.getLogger("resqai.alerts")

DELAY_ALERT_MIN = 15
ESCALATION_MIN = 30
SUPPRESSION_WINDOW_MIN = 10


async def create_alert(
    db: Any,
    alert_type: str,
    level: str,
    incident_id: str,
    message: str
) -> Optional[Dict[str, Any]]:
    """Create alert with 10-minute duplicate suppression, WebSocket broadcast, and multi-channel notifications."""
    now_dt = datetime.now(timezone.utc)
    suppress_threshold = now_dt - timedelta(minutes=SUPPRESSION_WINDOW_MIN)

    # 1. Check duplicate alert suppression within 10 minutes
    suppress_query = {
        "incident_id": str(incident_id),
        "type": alert_type,
        "created_at": {"$gte": suppress_threshold}
    }
    existing = await db.alerts.find_one(suppress_query)
    if existing:
        logger.info(f"Suppressed duplicate alert '{alert_type}' for incident '{incident_id}' (created within 10 min).")
        return None

    alert_id = f"ALT-{int(now_dt.timestamp() * 1000)}"
    alert_doc = {
        "_id": ObjectId(),
        "alert_id": alert_id,
        "type": alert_type,
        "level": level.lower(),
        "incident_id": str(incident_id),
        "message": message,
        "acknowledged": False,
        "acknowledged_at": None,
        "created_at": now_dt
    }

    await db.alerts.insert_one(alert_doc)
    formatted_alert = dict(alert_doc)
    formatted_alert["id"] = str(formatted_alert["_id"])
    formatted_alert["_id"] = str(formatted_alert["_id"])
    formatted_alert["created_at"] = now_dt.isoformat()

    # 2. Broadcast WebSocket alert_created event
    await ws_manager.broadcast_event(WebSocketEventType.ALERT_CREATED, formatted_alert)

    # 3. Route multi-channel notifications
    await NotificationService.route_alert_notifications(db, alert_doc)

    return formatted_alert


async def evaluate_delayed_and_escalation_checks(
    db: Any,
    demo_time_scale: float = 1.0,
    time_offset: Optional[timedelta] = None
) -> int:
    """Evaluate unresolved incidents for delayed response and escalation alerts."""
    now_dt = datetime.now(timezone.utc)
    if time_offset:
        now_dt = now_dt + time_offset

    delay_threshold_min = max(0.5, DELAY_ALERT_MIN / demo_time_scale)
    escalation_threshold_min = max(1.0, ESCALATION_MIN / demo_time_scale)

    unresolved_query = {
        "status": {"$in": ["new", "triaged", "dispatched", "en_route", "REPORTED", "VERIFIED", "DISPATCHED", "IN_PROGRESS"]}
    }

    cursor = db.incidents.find(unresolved_query)
    incidents = await cursor.to_list(length=200)

    alerts_created_count = 0

    for inc in incidents:
        inc_id = str(inc.get("incident_id") or inc.get("_id"))
        created_at = inc.get("created_at") or inc.get("reported_at") or now_dt
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        elapsed_min = (now_dt - created_at).total_seconds() / 60.0
        status_curr = str(inc.get("status", "")).lower()
        severity_curr = str(inc.get("severity", "")).lower()
        assigned_resources = inc.get("assigned_resources", [])

        # Check Delayed Response (new/triaged/dispatched for > delay_threshold_min without reaching on_scene)
        if status_curr in ["new", "triaged", "dispatched", "reported", "verified"] and elapsed_min >= delay_threshold_min:
            msg = f"Delayed response warning: Incident {inc_id} in status '{status_curr}' for {int(elapsed_min)} min without on-scene arrival."
            alt = await create_alert(db, "delayed_response", "warning", inc_id, msg)
            if alt:
                alerts_created_count += 1

        # Check Escalation (> escalation_threshold_min unresolved or critical with no assignments > 3 min)
        is_critical_unassigned = (severity_curr == "critical" and not assigned_resources and elapsed_min >= (3.0 / demo_time_scale))
        is_long_unresolved = (elapsed_min >= escalation_threshold_min and status_curr != "on_scene")

        if is_critical_unassigned or is_long_unresolved:
            msg = f"CRITICAL ESCALATION: Incident {inc_id} requires immediate senior officer intervention (unresolved for {int(elapsed_min)} min)."
            alt = await create_alert(db, "escalation", "critical", inc_id, msg)
            if alt:
                alerts_created_count += 1

    return alerts_created_count
