from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class IncidentSource(str, Enum):
    CITIZEN = "citizen"
    CITIZEN_CALL = "citizen_call"
    CALL_CENTER = "call_center"
    CALL_911 = "call_911"
    EMERGENCY_HOTLINE = "emergency_hotline"
    IOT = "iot"
    IOT_SENSOR = "iot_sensor"
    HAZMAT_ALERT = "hazmat_alert"
    FIELD_TEAM = "field_team"
    FIELD_UNIT = "field_unit"
    HOSPITAL = "hospital"
    GOVERNMENT = "government"
    SIMULATION = "simulation"
    SOCIAL_MEDIA = "social_media"


class IncidentType(str, Enum):
    FIRE = "fire"
    FLOOD = "flood"
    ROAD_ACCIDENT = "road_accident"
    MEDICAL_EMERGENCY = "medical_emergency"
    INDUSTRIAL_HAZARD = "industrial_hazard"
    BUILDING_COLLAPSE = "building_collapse"
    GAS_LEAK = "gas_leak"
    EARTHQUAKE = "earthquake"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    REPORTED = "REPORTED"
    VERIFIED = "VERIFIED"
    DISPATCHED = "DISPATCHED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    resolved = "resolved"
    closed = "closed"


class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., description="[longitude, latitude] in decimal degrees")


class TimelineEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str = Field(default="Event Recorded")
    actor: str = "System"
    details: Optional[str] = None

    def __init__(self, **data):
        if "event" in data and "action" not in data:
            data["action"] = data.pop("event")
        if "notes" in data and "details" not in data:
            data["details"] = data.pop("notes")
        super().__init__(**data)


class IncidentModel(BaseModel):
    incident_id: str = Field(..., description="Formatted incident identifier e.g. INC-1001")
    source: IncidentSource = Field(default=IncidentSource.CITIZEN)
    type: IncidentType = Field(default=IncidentType.OTHER)
    title: str
    description: str
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM)
    priority: IncidentPriority = Field(default=IncidentPriority.P3)
    status: IncidentStatus = Field(default=IncidentStatus.REPORTED)
    location: GeoPoint
    address: str
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    duplicate_of: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    assigned_resources: List[str] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
