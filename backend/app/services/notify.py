import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any, Optional
from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.models import (
    AlertLevel,
    NotificationChannel,
    NotificationStatus,
)
from app.schemas import doc_to_notification_out
from app.services.realtime import broadcast

logger = logging.getLogger("resqai.notify")


class NotificationService:
    """
    Multi-channel notification dispatcher:
    - in_app: real-time broadcast and DB storage
    - email: SMTP if configured, otherwise simulated
    - sms: simulated provider (Twilio / SMS Gateway drop-in)
    - push: simulated provider (FCM / WebPush drop-in)
    """

    @staticmethod
    async def send(
        db: AsyncDatabase,
        channel: NotificationChannel,
        recipient: str,
        subject: str,
        body: str,
        alert_id: Optional[ObjectId] = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        status = NotificationStatus.SIMULATED

        if channel == NotificationChannel.IN_APP:
            status = NotificationStatus.SENT
        elif channel == NotificationChannel.EMAIL:
            smtp_host = os.environ.get("SMTP_HOST")
            if smtp_host:
                try:
                    smtp_port = int(os.environ.get("SMTP_PORT", 587))
                    smtp_user = os.environ.get("SMTP_USER")
                    smtp_pass = os.environ.get("SMTP_PASS")
                    msg = MIMEText(body)
                    msg["Subject"] = subject
                    msg["From"] = smtp_user or "alerts@resqai.demo"
                    msg["To"] = recipient

                    with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
                        if smtp_user and smtp_pass:
                            server.starttls()
                            server.login(smtp_user, smtp_pass)
                        server.sendmail(msg["From"], [recipient], msg.as_string())
                    status = NotificationStatus.SENT
                except Exception as exc:
                    logger.warning("SMTP email send failed: %s. Storing as simulated.", exc)
                    status = NotificationStatus.SIMULATED
            else:
                logger.info("[SIMULATED EMAIL] To: %s | Subject: %s | Body: %s", recipient, subject, body[:80])
                status = NotificationStatus.SIMULATED
        elif channel == NotificationChannel.SMS:
            logger.info("[SIMULATED SMS] To: %s | Text: %s", recipient, body[:80])
            status = NotificationStatus.SIMULATED
        elif channel == NotificationChannel.PUSH:
            logger.info("[SIMULATED PUSH] Device: %s | Title: %s", recipient, subject)
            status = NotificationStatus.SIMULATED

        notif_doc: dict[str, Any] = {
            "_id": ObjectId(),
            "channel": channel,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "status": status,
            "alert_id": alert_id,
            "created_at": now,
        }

        await db["notifications"].insert_one(notif_doc)

        # Broadcast in-app and general notification events
        out_schema = doc_to_notification_out(notif_doc)
        await broadcast("notification_created", out_schema.model_dump(mode="json"))

        return notif_doc

    @classmethod
    async def dispatch_alert_notifications(
        cls,
        db: AsyncDatabase,
        alert_doc: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Dispatches notifications to appropriate channels based on alert level:
        - info -> in_app
        - warning -> in_app + push
        - critical -> in_app + push + sms + email
        """
        level = AlertLevel(alert_doc["level"])
        alert_id = alert_doc["_id"]
        subject = f"ResQAI [{level.value.upper()} ALERT]: {alert_doc['type']}"
        body = alert_doc["message"]

        dispatched: list[dict[str, Any]] = []

        # 1. in_app (all levels)
        dispatched.append(
            await cls.send(
                db,
                channel=NotificationChannel.IN_APP,
                recipient="dispatch_console",
                subject=subject,
                body=body,
                alert_id=alert_id,
            )
        )

        # 2. push (warning & critical)
        if level in (AlertLevel.WARNING, AlertLevel.CRITICAL):
            dispatched.append(
                await cls.send(
                    db,
                    channel=NotificationChannel.PUSH,
                    recipient="field_responders_app_topic",
                    subject=subject,
                    body=body,
                    alert_id=alert_id,
                )
            )

        # 3. sms & email (critical only)
        if level == AlertLevel.CRITICAL:
            dispatched.append(
                await cls.send(
                    db,
                    channel=NotificationChannel.SMS,
                    recipient="+91-9876543210",
                    subject=subject,
                    body=body,
                    alert_id=alert_id,
                )
            )
            dispatched.append(
                await cls.send(
                    db,
                    channel=NotificationChannel.EMAIL,
                    recipient="duty.officer@resqai.demo",
                    subject=subject,
                    body=body,
                    alert_id=alert_id,
                )
            )

        return dispatched
