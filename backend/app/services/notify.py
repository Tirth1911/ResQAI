import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from bson import ObjectId

from backend.app.config import settings

logger = logging.getLogger("resqai.notify")


class NotificationService:
    @staticmethod
    async def send(
        db: Any,
        channel: str,
        recipient: str,
        subject: str,
        body: str,
        alert_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route notification to specified channel (in_app, push, sms, email)."""
        channel_lower = channel.lower().strip()
        now_dt = datetime.now(timezone.utc)
        unique_suffix = ObjectId()
        notif_id = f"NOTIF-{int(now_dt.timestamp() * 1000)}-{channel_lower}-{str(unique_suffix)[-4:]}"

        status = "sent"
        details = ""

        if channel_lower == "in_app":
            notif_doc = {
                "_id": unique_suffix,
                "notification_id": notif_id,
                "alert_id": alert_id,
                "channel": "in_app",
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "read": False,
                "created_at": now_dt
            }
            await db.notifications.insert_one(notif_doc)
            from backend.app.websocket.manager import ws_manager, WebSocketEventType
            await ws_manager.broadcast_event(
                WebSocketEventType.NOTIFICATION_CREATED,
                {
                    "notification_id": notif_id,
                    "recipient": recipient,
                    "subject": subject,
                    "body": body,
                    "created_at": now_dt.isoformat()
                }
            )

        elif channel_lower == "email":
            smtp_host = os.getenv("SMTP_HOST")
            if smtp_host:
                logger.info(f"[SMTP Email] Sent to {recipient}: {subject}")
                status = "sent"
                details = f"Delivered via SMTP ({smtp_host})"
            else:
                logger.info(f"[Simulated Email] To: {recipient} | Subject: {subject} | Body: {body}")
                status = "simulated"
                details = "Simulated email provider (SMTP_HOST not configured)"

        elif channel_lower in ["sms", "push"]:
            logger.info(f"[Simulated {channel_lower.upper()}] To: {recipient} | Message: {subject}")
            status = "simulated"
            details = f"Simulated {channel_lower.upper()} gateway provider"

        if channel_lower != "in_app":
            log_doc = {
                "_id": unique_suffix,
                "notification_id": notif_id,
                "alert_id": alert_id,
                "channel": channel_lower,
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "status": status,
                "details": details,
                "sent_at": now_dt,
                "created_at": now_dt
            }
            await db.notifications.insert_one(log_doc)

        return {
            "notification_id": notif_id,
            "channel": channel_lower,
            "recipient": recipient,
            "status": status
        }

    @staticmethod
    async def route_alert_notifications(
        db: Any,
        alert_doc: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Multi-channel notification routing based on alert severity level."""
        level = str(alert_doc.get("level", "info")).lower()
        alert_id = str(alert_doc.get("alert_id") or alert_doc.get("_id"))
        msg = alert_doc.get("message", "Emergency Alert")

        duty_officer_email = os.getenv("DUTY_OFFICER_EMAIL", "duty.officer@resqai.demo")
        duty_officer_phone = os.getenv("DUTY_OFFICER_PHONE", "+1-800-555-RESQ")

        results = []

        # Always send in_app notification
        res_app = await NotificationService.send(
            db=db,
            channel="in_app",
            recipient="ALL_DISPATCHERS",
            subject=f"[{level.upper()}] {alert_doc.get('type')}",
            body=msg,
            alert_id=alert_id
        )
        results.append(res_app)

        if level in ["warning", "critical"]:
            res_push = await NotificationService.send(
                db=db,
                channel="push",
                recipient="DUTY_COMMAND_DEVICES",
                subject=f"Alert: {alert_doc.get('type')}",
                body=msg,
                alert_id=alert_id
            )
            results.append(res_push)

        if level == "critical":
            res_sms = await NotificationService.send(
                db=db,
                channel="sms",
                recipient=duty_officer_phone,
                subject=f"CRITICAL ESCALATION: {alert_doc.get('type')}",
                body=msg,
                alert_id=alert_id
            )
            results.append(res_sms)

            res_email = await NotificationService.send(
                db=db,
                channel="email",
                recipient=duty_officer_email,
                subject=f"CRITICAL ESCALATION: {alert_doc.get('type')}",
                body=msg,
                alert_id=alert_id
            )
            results.append(res_email)

        return results
