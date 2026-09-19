from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    CRITICAL_INCIDENT = "CRITICAL_INCIDENT"
    P1_UNASSIGNED = "P1_UNASSIGNED"
    RESPONSE_DELAYED = "RESPONSE_DELAYED"
    NO_SUITABLE_RESOURCE = "NO_SUITABLE_RESOURCE"
    RESOURCE_SHORTAGE = "RESOURCE_SHORTAGE"
    INCIDENT_ESCALATED = "INCIDENT_ESCALATED"
    MULTIPLE_DUPLICATES = "MULTIPLE_DUPLICATES"
    GENERAL_ALERT = "GENERAL_ALERT"


class NotificationModel(BaseModel):
    alert_id: str = Field(..., description="Formatted alert identifier e.g. ALT-20260919-0001")
    notification_id: Optional[str] = None
    title: Optional[str] = None
    type: str = Field(default=AlertType.GENERAL_ALERT.value)
    severity: str = Field(default=AlertSeverity.INFO.value)
    incident_id: Optional[str] = None
    message: str
    target_role: str = "ALL"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False
