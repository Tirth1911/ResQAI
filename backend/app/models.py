from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional, Union
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated


# Domain Contract Enums (str Enum for seamless JSON serialization)
class IncidentType(str, Enum):
    FIRE = "fire"
    FLOOD = "flood"
    ACCIDENT = "accident"
    MEDICAL = "medical"
    INDUSTRIAL = "industrial"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


SEVERITY_PRIORITY_MAP: dict[IncidentSeverity, int] = {
    IncidentSeverity.CRITICAL: 1,
    IncidentSeverity.HIGH: 2,
    IncidentSeverity.MEDIUM: 3,
    IncidentSeverity.LOW: 4,
}


class IncidentStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    RESOLVED = "resolved"


class ReportSource(str, Enum):
    CITIZEN = "citizen"
    CALL_CENTER = "call_center"
    IOT_SENSOR = "iot_sensor"
    FIELD_TEAM = "field_team"
    HOSPITAL = "hospital"
    GOVERNMENT = "government"


class ResourceKind(str, Enum):
    FIRE_TRUCK = "fire_truck"
    AMBULANCE = "ambulance"
    POLICE_UNIT = "police_unit"
    RESCUE_TEAM = "rescue_team"
    DISASTER_RESPONSE_TEAM = "disaster_response_team"
    MEDICAL_KIT = "medical_kit"
    FIRE_EQUIPMENT = "fire_equipment"
    RESCUE_TOOLS = "rescue_tools"
    HOSPITAL = "hospital"
    RELIEF_CAMP = "relief_camp"
    CONTROL_CENTER = "control_center"


class ResourceStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    OFFLINE = "offline"


class AlertType(str, Enum):
    CRITICAL_INCIDENT = "critical_incident"
    DELAYED_RESPONSE = "delayed_response"
    RESOURCE_SHORTAGE = "resource_shortage"
    ESCALATION = "escalation"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    SENT = "sent"
    SIMULATED = "simulated"
    FAILED = "failed"


class AssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


def _validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError(f"Invalid ObjectId: {v}")


PyObjectId = Annotated[Union[ObjectId, str], BeforeValidator(_validate_object_id)]


# GeoJSON Point
class GeoJSONPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float] = Field(..., min_length=2, max_length=2)  # [longitude, latitude]


# Document Shapes for MongoDB Storage
class ReportDoc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: ReportSource
    reporter: Optional[str] = None
    raw_text: str
    location: GeoJSONPoint
    reported_at: datetime


class IncidentDoc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str
    description: str
    type: IncidentType
    severity: IncidentSeverity
    priority: int = 4
    status: IncidentStatus = IncidentStatus.NEW
    location: GeoJSONPoint
    address: Optional[str] = None
    source: ReportSource
    report_count: int = 1
    reports: list[ReportDoc] = Field(default_factory=list)
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    classified_by: Literal["llm", "rules"] = "rules"
    ai_assist: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class ResourceDoc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    kind: ResourceKind
    status: ResourceStatus = ResourceStatus.AVAILABLE
    location: GeoJSONPoint
    capacity: int
    capabilities: list[IncidentType]
    station: str
    updated_at: datetime


class AssignmentDoc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    incident_id: PyObjectId
    resource_id: PyObjectId
    status: AssignmentStatus = AssignmentStatus.ASSIGNED
    score: float
    distance_km: float
    eta_min: float
    assigned_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class AlertDoc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: AlertType
    level: AlertLevel
    incident_id: Optional[PyObjectId] = None
    message: str
    acknowledged: bool = False
    created_at: datetime


class NotificationDoc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    status: NotificationStatus = NotificationStatus.SIMULATED
    alert_id: Optional[PyObjectId] = None
    created_at: datetime
