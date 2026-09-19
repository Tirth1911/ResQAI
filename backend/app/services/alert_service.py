import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from backend.app.config import settings
from backend.app.models.notification import AlertSeverity, AlertType, NotificationModel
from backend.app.websocket.manager import ws_manager, WebSocketEventType

logger = logging.getLogger("resqai.alert_service")


# =============================================================================
# 1. EMAIL & SMS SERVICE ABSTRACTIONS
# =============================================================================

class BaseEmailProvider(ABC):
    @abstractmethod
    async def send_email(self, recipient: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        pass


class SimulatedEmailProvider(BaseEmailProvider):
    """Zero-cost local simulated email delivery service for hackathon MVP."""

    async def send_email(self, recipient: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        logger.info(f"[SIMULATED EMAIL DISPATCH] To: {recipient} | Subject: '{subject}' | Message: {body_text[:120]}...")
        return True


class BaseSMSProvider(ABC):
    @abstractmethod
    async def send_sms(self, phone_number: str, message: str) -> bool:
        pass


class SimulatedSMSProvider(BaseSMSProvider):
    """Zero-cost local simulated SMS delivery service for hackathon MVP."""

    async def send_sms(self, phone_number: str, message: str) -> bool:
        logger.info(f"[SIMULATED SMS DISPATCH] To: {phone_number} | Message: '{message}'")
        return True


# Provider Singletons
email_provider: BaseEmailProvider = SimulatedEmailProvider()
sms_provider: BaseSMSProvider = SimulatedSMSProvider()


# =============================================================================
# 2. ALERT & ESCALATION ENGINE
# =============================================================================

class AlertService:

    @classmethod
    async def generate_alert_id(cls, db: AsyncIOMotorDatabase) -> str:
        """Generate unique human-readable alert identifier: ALT-YYYYMMDD-XXXX."""
        now = datetime.now(timezone.utc)
        date_prefix = now.strftime("%Y%m%d")
        count = await db.notifications.count_documents({})
        return f"ALT-{date_prefix}-{count + 1:04d}"

    @classmethod
    async def create_alert(
        cls,
        db: AsyncIOMotorDatabase,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        incident_id: Optional[str] = None,
        title: Optional[str] = None,
        target_role: str = "ALL",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create, persist, and multi-channel broadcast an emergency alert/notification.
        1. Generates unique alert_id (ALT-YYYYMMDD-XXXX).
        2. Persists to MongoDB notifications collection.
        3. Delivers via simulated/real Email & SMS channels.
        4. Broadcasts real-time WebSocket event to all dashboard clients.
        """
        now_utc = datetime.now(timezone.utc)
        alert_id = await cls.generate_alert_id(db)
        resolved_title = title or f"{severity.value} Emergency Alert: {alert_type.value}"

        doc = {
            "alert_id": alert_id,
            "notification_id": alert_id,
            "title": resolved_title,
            "type": alert_type.value if hasattr(alert_type, "value") else str(alert_type),
            "severity": severity.value if hasattr(severity, "value") else str(severity),
            "incident_id": incident_id,
            "message": message,
            "target_role": target_role,
            "metadata": metadata or {},
            "created_at": now_utc,
            "read": False
        }

        res = await db.notifications.insert_one(doc)
        doc["_id"] = str(res.inserted_id)

        # Multi-Channel Dispatch (Simulated Email & SMS)
        if severity in [AlertSeverity.CRITICAL, AlertSeverity.WARNING]:
            await email_provider.send_email(
                recipient="emergency-command@gujarat-disaster.gov.in",
                subject=f"[ResQAI {severity.value}] {resolved_title}",
                body_text=f"Alert ID: {alert_id}\nIncident: {incident_id or 'General'}\nDetails: {message}"
            )
            await sms_provider.send_sms(
                phone_number="+91-112-EMERGENCY",
                message=f"[ResQAI {severity.value}] {alert_id} (Inc: {incident_id or 'N/A'}): {message[:100]}"
            )

        # WebSocket real-time broadcast
        await ws_manager.broadcast_event(
            WebSocketEventType.NOTIFICATION_CREATED,
            doc
        )

        return doc

    # -------------------------------------------------------------------------
    # 7 ALERT EVALUATION SCENARIOS
    # -------------------------------------------------------------------------

    @classmethod
    async def evaluate_incident_alerts(cls, db: AsyncIOMotorDatabase, incident: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate incident for all alert triggers upon creation or state mutation:
        1. Incident severity is CRITICAL
        2. P1 incident remains unassigned
        3. Incident escalated to CRITICAL/P1
        4. Incident receives multiple duplicate reports (>= 3)
        """
        alerts_generated = []
        inc_id = incident.get("incident_id", str(incident.get("_id", "N/A")))
        severity = str(incident.get("severity", "")).upper()
        priority = str(incident.get("priority", "")).upper()
        assigned = incident.get("assigned_resources", [])
        duplicate_count = incident.get("duplicate_count", 0)

        # Condition 1: Incident severity is CRITICAL
        if severity == "CRITICAL":
            alert = await cls.create_alert(
                db=db,
                alert_type=AlertType.CRITICAL_INCIDENT,
                severity=AlertSeverity.CRITICAL,
                incident_id=inc_id,
                title=f"CRITICAL SEVERITY: {incident.get('title', 'Emergency Incident')}",
                message=f"Critical emergency reported at {incident.get('address', 'active coordinates')}. Immediate priority triage required."
            )
            alerts_generated.append(alert)

        # Condition 2: P1 incident remains unassigned
        if priority == "P1" and len(assigned) == 0:
            alert = await cls.create_alert(
                db=db,
                alert_type=AlertType.P1_UNASSIGNED,
                severity=AlertSeverity.CRITICAL,
                incident_id=inc_id,
                title=f"P1 UNASSIGNED EMERGENCY: {inc_id}",
                message=f"Priority P1 incident '{incident.get('title')}' is currently unassigned! Immediate responder dispatch required."
            )
            alerts_generated.append(alert)

        # Condition 7: Incident receives multiple duplicate reports (>= 3)
        if duplicate_count >= 3:
            alert = await cls.create_alert(
                db=db,
                alert_type=AlertType.MULTIPLE_DUPLICATES,
                severity=AlertSeverity.WARNING,
                incident_id=inc_id,
                title=f"HIGH INCOMING CALL VOLUME: {inc_id}",
                message=f"Incident '{inc_id}' has received {duplicate_count} duplicate distress reports. Incident magnitude may be growing."
            )
            alerts_generated.append(alert)

        return alerts_generated

    @classmethod
    async def check_delayed_responses(cls, db: AsyncIOMotorDatabase, threshold_minutes: int = 15) -> List[Dict[str, Any]]:
        """
        Condition 3: Response is delayed
        Scans for unresolved incidents reported > threshold_minutes ago that remain in REPORTED status.
        """
        now_utc = datetime.now(timezone.utc)
        cutoff_time = now_utc - timedelta(minutes=threshold_minutes)

        cursor = db.incidents.find({
            "status": "REPORTED",
            "reported_at": {"$lte": cutoff_time}
        })

        delayed_alerts = []
        async for inc in cursor:
            inc_id = inc.get("incident_id", str(inc.get("_id")))
            reported_time = inc.get("reported_at", cutoff_time)
            if isinstance(reported_time, datetime) and reported_time.tzinfo is None:
                reported_time = reported_time.replace(tzinfo=timezone.utc)

            elapsed_min = int(abs((now_utc - reported_time).total_seconds()) / 60.0)

            alert = await cls.create_alert(
                db=db,
                alert_type=AlertType.RESPONSE_DELAYED,
                severity=AlertSeverity.WARNING if inc.get("severity") != "CRITICAL" else AlertSeverity.CRITICAL,
                incident_id=inc_id,
                title=f"RESPONSE DELAYED: {inc_id} ({elapsed_min}m pending)",
                message=f"Incident '{inc.get('title')}' has been in REPORTED status for {elapsed_min} minutes without verification or dispatch."
            )
            delayed_alerts.append(alert)

        return delayed_alerts

    @classmethod
    async def trigger_resource_shortage_alert(
        cls,
        db: AsyncIOMotorDatabase,
        incident_id: str,
        incident_type: str,
        required_category: str = "AMBULANCE"
    ) -> Dict[str, Any]:
        """
        Conditions 4 & 5: No suitable resource is available / Resource shortage detected.
        """
        return await cls.create_alert(
            db=db,
            alert_type=AlertType.RESOURCE_SHORTAGE,
            severity=AlertSeverity.CRITICAL,
            incident_id=incident_id,
            title=f"RESOURCE SHORTAGE: No available {required_category} units",
            message=f"Zero available {required_category} responders found within operational radius for incident {incident_id} ({incident_type}). Secondary agency aid required."
        )

    @classmethod
    async def trigger_escalation_alert(
        cls,
        db: AsyncIOMotorDatabase,
        incident_id: str,
        old_severity: str,
        new_severity: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Condition 6: Incident escalates to a higher severity/priority.
        """
        return await cls.create_alert(
            db=db,
            alert_type=AlertType.INCIDENT_ESCALATED,
            severity=AlertSeverity.CRITICAL if new_severity.upper() == "CRITICAL" else AlertSeverity.WARNING,
            incident_id=incident_id,
            title=f"INCIDENT ESCALATION: {incident_id} -> {new_severity.upper()}",
            message=f"Incident {incident_id} escalated from {old_severity} to {new_severity.upper()}. {reason or 'Additional casualties or hazard spread detected.'}"
        )
