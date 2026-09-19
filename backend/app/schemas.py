from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.db import from_geojson, serialize_doc
from app.models import (
    AlertLevel,
    AlertType,
    AssignmentStatus,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    NotificationChannel,
    NotificationStatus,
    ReportSource,
    ResourceKind,
    ResourceStatus,
)


# ==============================================================================
# Report Schemas
# ==============================================================================

class ReportIn(BaseModel):
    source: ReportSource
    reporter: Optional[str] = None
    text: str
    lat: float
    lng: float
    address: Optional[str] = None
    reported_at: Optional[datetime] = None
    extra: Optional[dict[str, Any]] = None


class ReportCreate(BaseModel):
    source: ReportSource = ReportSource.CITIZEN
    reporter: Optional[str] = None
    raw_text: str
    lat: float
    lng: float
    reported_at: Optional[datetime] = None


class ReportOut(BaseModel):
    source: ReportSource
    reporter: Optional[str] = None
    raw_text: str
    lat: float
    lng: float
    reported_at: datetime


class ReportResponse(BaseModel):
    incident_id: str
    merged: bool = False
    duplicate_score: Optional[float] = None
    incident: "IncidentOut"


# ==============================================================================
# Incident Schemas
# ==============================================================================

class IncidentCreate(BaseModel):
    title: str
    description: str
    type: IncidentType
    severity: IncidentSeverity
    lat: float
    lng: float
    address: Optional[str] = None
    source: ReportSource = ReportSource.CITIZEN
    reporter: Optional[str] = None


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    type: IncidentType
    severity: IncidentSeverity
    priority: int
    status: IncidentStatus
    lat: float
    lng: float
    address: Optional[str] = None
    source: ReportSource
    report_count: int = 1
    reports: list[ReportOut] = Field(default_factory=list)
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    classified_by: str = "rules"
    ai_assist: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class IncidentDetailOut(IncidentOut):
    assignments: list["AssignmentOut"] = Field(default_factory=list)


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


# ==============================================================================
# Resource Schemas
# ==============================================================================

class ResourceSummary(BaseModel):
    id: str
    name: str
    kind: ResourceKind
    status: ResourceStatus
    station: str


class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    kind: ResourceKind
    status: ResourceStatus
    lat: float
    lng: float
    capacity: int
    capabilities: list[IncidentType]
    station: str
    updated_at: datetime


# ==============================================================================
# Assignment Schemas
# ==============================================================================

class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    resource_id: str
    status: AssignmentStatus
    score: float
    distance_km: float
    eta_min: float
    assigned_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    resource: Optional[ResourceSummary] = None


class AssignmentStatusUpdate(BaseModel):
    status: AssignmentStatus


# ==============================================================================
# Recommendation & Dispatch Schemas
# ==============================================================================

class RecommendationItem(BaseModel):
    resource: ResourceOut
    score: float
    distance_km: float
    eta_min: float
    reason: str


class RecommendationsOut(BaseModel):
    units: list[RecommendationItem]
    hospital: Optional[ResourceOut] = None
    relief_camp: Optional[ResourceOut] = None
    shortage: bool = False
    shortage_detail: Optional[str] = None


class DispatchRequest(BaseModel):
    resource_ids: Optional[list[str]] = None
    auto: bool = False


class DispatchResponse(BaseModel):
    incident: IncidentOut
    assignments: list[AssignmentOut]
    skipped: list[str] = Field(default_factory=list)


# ==============================================================================
# Alert & Notification Schemas
# ==============================================================================

class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: AlertType
    level: AlertLevel
    incident_id: Optional[str] = None
    message: str
    acknowledged: bool = False
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    status: NotificationStatus
    alert_id: Optional[str] = None
    created_at: datetime


# ==============================================================================
# Document -> Schema Mapper Functions
# ==============================================================================

def doc_to_report_out(doc: dict[str, Any]) -> ReportOut:
    serialized = serialize_doc(doc)
    lat = serialized.get("lat")
    lng = serialized.get("lng")
    if lat is None or lng is None:
        coords = from_geojson(serialized)
        lat = coords["lat"]
        lng = coords["lng"]
    return ReportOut(
        source=serialized["source"],
        reporter=serialized.get("reporter"),
        raw_text=serialized["raw_text"],
        lat=float(lat),
        lng=float(lng),
        reported_at=serialized["reported_at"],
    )


def doc_to_incident_out(doc: dict[str, Any]) -> IncidentOut:
    serialized = serialize_doc(doc)
    lat = serialized.get("lat")
    lng = serialized.get("lng")
    if lat is None or lng is None:
        coords = from_geojson(serialized)
        lat = coords["lat"]
        lng = coords["lng"]

    reports_data = [doc_to_report_out(r) for r in serialized.get("reports", [])]

    return IncidentOut(
        id=str(serialized["id"]),
        title=serialized["title"],
        description=serialized["description"],
        type=serialized["type"],
        severity=serialized["severity"],
        priority=serialized.get("priority", 4),
        status=serialized.get("status", IncidentStatus.NEW),
        lat=float(lat),
        lng=float(lng),
        address=serialized.get("address"),
        source=serialized["source"],
        report_count=serialized.get("report_count", 1),
        reports=reports_data,
        ai_confidence=serialized.get("ai_confidence"),
        ai_reasoning=serialized.get("ai_reasoning"),
        classified_by=serialized.get("classified_by", "rules"),
        ai_assist=serialized.get("ai_assist"),
        created_at=serialized["created_at"],
        updated_at=serialized["updated_at"],
        resolved_at=serialized.get("resolved_at"),
    )


def doc_to_resource_out(doc: dict[str, Any]) -> ResourceOut:
    serialized = serialize_doc(doc)
    lat = serialized.get("lat")
    lng = serialized.get("lng")
    if lat is None or lng is None:
        coords = from_geojson(serialized)
        lat = coords["lat"]
        lng = coords["lng"]

    return ResourceOut(
        id=str(serialized["id"]),
        name=serialized["name"],
        kind=serialized["kind"],
        status=serialized.get("status", ResourceStatus.AVAILABLE),
        lat=float(lat),
        lng=float(lng),
        capacity=serialized["capacity"],
        capabilities=serialized.get("capabilities", []),
        station=serialized["station"],
        updated_at=serialized["updated_at"],
    )


def doc_to_assignment_out(
    doc: dict[str, Any],
    resource_doc: Optional[dict[str, Any]] = None,
) -> AssignmentOut:
    serialized = serialize_doc(doc)
    resource_summary: Optional[ResourceSummary] = None

    res_src = resource_doc or serialized.get("resource")
    if res_src:
        res_ser = serialize_doc(res_src)
        resource_summary = ResourceSummary(
            id=str(res_ser["id"]),
            name=res_ser["name"],
            kind=res_ser["kind"],
            status=res_ser.get("status", ResourceStatus.AVAILABLE),
            station=res_ser["station"],
        )

    return AssignmentOut(
        id=str(serialized["id"]),
        incident_id=str(serialized["incident_id"]),
        resource_id=str(serialized["resource_id"]),
        status=serialized["status"],
        score=float(serialized.get("score", 0.0)),
        distance_km=float(serialized.get("distance_km", 0.0)),
        eta_min=float(serialized.get("eta_min", 0.0)),
        assigned_at=serialized["assigned_at"],
        updated_at=serialized["updated_at"],
        completed_at=serialized.get("completed_at"),
        resource=resource_summary,
    )


def doc_to_alert_out(doc: dict[str, Any]) -> AlertOut:
    serialized = serialize_doc(doc)
    incident_id = serialized.get("incident_id")
    return AlertOut(
        id=str(serialized["id"]),
        type=serialized["type"],
        level=serialized["level"],
        incident_id=str(incident_id) if incident_id else None,
        message=serialized["message"],
        acknowledged=bool(serialized.get("acknowledged", False)),
        created_at=serialized["created_at"],
    )


def doc_to_notification_out(doc: dict[str, Any]) -> NotificationOut:
    serialized = serialize_doc(doc)
    alert_id = serialized.get("alert_id")
    return NotificationOut(
        id=str(serialized["id"]),
        channel=serialized["channel"],
        recipient=serialized["recipient"],
        subject=serialized["subject"],
        body=serialized["body"],
        status=serialized["status"],
        alert_id=str(alert_id) if alert_id else None,
        created_at=serialized["created_at"],
    )
