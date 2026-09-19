import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.config import settings
from app.models import (
    AlertLevel,
    AlertType,
    AssignmentStatus,
    IncidentSeverity,
    IncidentStatus,
)
from app.schemas import doc_to_alert_out
from app.services.notify import NotificationService
from app.services.realtime import broadcast

logger = logging.getLogger("resqai.alerts")


async def create_alert(
    db: AsyncDatabase,
    type: AlertType,
    level: AlertLevel,
    incident_id: Optional[ObjectId],
    message: str,
    now: Optional[datetime] = None,
) -> Optional[dict[str, Any]]:
    """
    Creates an alert document, enforces 10-minute duplicate suppression per incident/type,
    triggers multi-channel notifications, and broadcasts alert_created.
    """
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    # 1. Duplicate suppression: no duplicate alert of same type for incident within 10 min
    if incident_id:
        ten_min_ago = current_time - timedelta(minutes=10)
        existing = await db["alerts"].find_one({
            "incident_id": incident_id,
            "type": type,
            "created_at": {"$gte": ten_min_ago},
        })
        if existing:
            logger.debug(
                "Suppressed duplicate alert '%s' for incident %s (last within 10m)",
                type,
                incident_id,
            )
            return None

    alert_doc: dict[str, Any] = {
        "_id": ObjectId(),
        "type": type,
        "level": level,
        "incident_id": incident_id,
        "message": message,
        "acknowledged": False,
        "created_at": current_time,
    }

    await db["alerts"].insert_one(alert_doc)
    logger.info("Alert created [%s - %s]: %s", level.value, type.value, message)

    # 2. Trigger multi-channel notifications
    await NotificationService.dispatch_alert_notifications(db, alert_doc)

    # 3. Broadcast real-time event
    out_schema = doc_to_alert_out(alert_doc)
    await broadcast("alert_created", out_schema.model_dump(mode="json"))

    return alert_doc


async def run_alert_checks(
    db: AsyncDatabase,
    now: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    """
    Evaluates delayed response and escalation rules across all active incidents.
    Supports DEMO_TIME_SCALE to accelerate thresholds for demonstrations and tests.
    """
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    time_scale = max(0.01, float(settings.DEMO_TIME_SCALE))
    delay_limit_min = settings.DELAY_ALERT_MIN / time_scale
    escalation_limit_min = settings.ESCALATION_MIN / time_scale
    critical_no_asg_limit_min = 3.0 / time_scale

    created_alerts: list[dict[str, Any]] = []

    # Query active, unresolved incidents
    cursor = db["incidents"].find({"status": {"$ne": IncidentStatus.RESOLVED}})
    active_incidents = [doc async for doc in cursor]

    for inc in active_incidents:
        inc_id = inc["_id"]
        created_at = inc.get("created_at")
        if created_at is None:
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        age_min = (current_time - created_at).total_seconds() / 60.0
        if age_min <= 0:
            continue
        status = IncidentStatus(inc.get("status", IncidentStatus.NEW))
        severity = IncidentSeverity(inc.get("severity", IncidentSeverity.MEDIUM))

        # Check existing assignments for this incident
        asg_cursor = db["assignments"].find({"incident_id": inc_id})
        assignments = [a async for a in asg_cursor]

        has_on_scene = any(a.get("status") in (AssignmentStatus.ON_SCENE, AssignmentStatus.COMPLETED) for a in assignments)
        has_any_asg = len(assignments) > 0

        # Rule 1: Escalation for critical incident with no assignments after 3 min
        if severity == IncidentSeverity.CRITICAL and not has_any_asg and age_min >= critical_no_asg_limit_min:
            msg = (
                f"CRITICAL ESCALATION: Critical incident '{inc.get('title')}' has had zero units "
                f"assigned after {age_min:.1f} minutes. Urgent dispatch command required."
            )
            alert = await create_alert(
                db,
                type=AlertType.ESCALATION,
                level=AlertLevel.CRITICAL,
                incident_id=inc_id,
                message=msg,
                now=current_time,
            )
            if alert:
                created_alerts.append(alert)
            continue

        # Rule 2: Escalation if unresolved and not on_scene after ESCALATION_MIN
        if not has_on_scene and age_min >= escalation_limit_min:
            msg = (
                f"CRITICAL ESCALATION: Incident '{inc.get('title')}' remains unresolved with no unit on scene "
                f"after {age_min:.1f} minutes. Escalating to District Collector / Senior Command."
            )
            alert = await create_alert(
                db,
                type=AlertType.ESCALATION,
                level=AlertLevel.CRITICAL,
                incident_id=inc_id,
                message=msg,
                now=current_time,
            )
            if alert:
                created_alerts.append(alert)
            continue

        # Rule 3: Delayed response if new/triaged/dispatched for > DELAY_ALERT_MIN without on_scene
        if status in (IncidentStatus.NEW, IncidentStatus.TRIAGED, IncidentStatus.DISPATCHED) and not has_on_scene and age_min >= delay_limit_min:
            msg = (
                f"DELAYED RESPONSE WARNING: Incident '{inc.get('title')}' in state '{status.value}' "
                f"for {age_min:.1f} minutes without units on scene."
            )
            alert = await create_alert(
                db,
                type=AlertType.DELAYED_RESPONSE,
                level=AlertLevel.WARNING,
                incident_id=inc_id,
                message=msg,
                now=current_time,
            )
            if alert:
                created_alerts.append(alert)

    return created_alerts
