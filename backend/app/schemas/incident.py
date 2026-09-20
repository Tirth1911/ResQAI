from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator
from backend.app.models.incident import (
    IncidentSource,
    IncidentType,
    IncidentSeverity,
    IncidentPriority,
    IncidentStatus,
    GeoPoint,
    TimelineEvent,
)


class IncidentLocationInput(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    address: Optional[str] = Field(None, description="Street address or landmark description")


class IncidentCreate(BaseModel):
    title: Optional[str] = Field(default=None, description="Brief summary of the emergency")
    description: str = Field(..., min_length=3, description="Detailed description of what is happening")
    source: IncidentSource = Field(default=IncidentSource.CITIZEN, description="Reporting channel")
    type: Optional[IncidentType] = Field(default=None, description="Incident category (if omitted, AI classification is performed)")
    severity: Optional[IncidentSeverity] = Field(default=None, description="Severity ranking (if omitted, estimated by AI)")
    priority: Optional[IncidentPriority] = Field(default=None, description="Dispatch priority P1-P4 (if omitted, assigned by AI)")
    status: Optional[IncidentStatus] = Field(default=IncidentStatus.REPORTED, description="Initial incident status")
    location: Optional[Any] = Field(default=None, description="Geographical coordinates or address string")
    address: Optional[str] = Field(default=None, description="Explicit address string")
    reported_at: Optional[datetime] = Field(default=None, description="Report timestamp (defaults to current UTC time)")
    assigned_resources: List[str] = Field(default_factory=list, description="Initial assigned resource IDs")
    duplicate_of: Optional[str] = Field(default=None, description="Master incident ID if known duplicate")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        
        # 1. Normalize title if missing
        if not data.get("title") and data.get("description"):
            desc = data["description"].strip()
            first_sent = desc.split(".")[0].split("\n")[0]
            data["title"] = (first_sent[:90] + "...") if len(first_sent) > 90 else first_sent
            if len(data["title"]) < 3:
                data["title"] = "Emergency Incident Report"

        # 2. Normalize location
        loc = data.get("location")
        if isinstance(loc, str):
            addr_str = loc
            lat, lon = 23.0225, 72.5714  # Ahmedabad center default
            addr_lower = addr_str.lower()
            if "odhav" in addr_lower:
                lat, lon = 23.0310, 72.6560
            elif "highway" in addr_lower or "iscon" in addr_lower:
                lat, lon = 23.0290, 72.5070
            elif "naroda" in addr_lower:
                lat, lon = 23.0710, 72.6550
            elif "subhash" in addr_lower or "river" in addr_lower:
                lat, lon = 23.0610, 72.5850
            elif "navrangpura" in addr_lower:
                lat, lon = 23.0360, 72.5610
            data["location"] = IncidentLocationInput(latitude=lat, longitude=lon, address=addr_str)
            if not data.get("address"):
                data["address"] = addr_str
        elif isinstance(loc, dict):
            lat = loc.get("latitude") or loc.get("lat") or 23.0225
            lon = loc.get("longitude") or loc.get("lng") or loc.get("lon") or 72.5714
            addr = loc.get("address") or data.get("address")
            data["location"] = IncidentLocationInput(latitude=float(lat), longitude=float(lon), address=addr)
        elif loc is None:
            # Fallback from flat lat/lng or address
            lat = data.get("lat") or data.get("latitude") or 23.0225
            lon = data.get("lng") or data.get("lon") or data.get("longitude") or 72.5714
            addr = data.get("address") or f"Lat: {lat}, Lon: {lon}"
            data["location"] = IncidentLocationInput(latitude=float(lat), longitude=float(lon), address=addr)

        return data


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=5)
    source: Optional[IncidentSource] = None
    type: Optional[IncidentType] = None
    severity: Optional[IncidentSeverity] = None
    priority: Optional[IncidentPriority] = None
    status: Optional[IncidentStatus] = None
    address: Optional[str] = None
    location: Optional[IncidentLocationInput] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    duplicate_of: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    assigned_resources: Optional[List[str]] = None


class IncidentActionRequest(BaseModel):
    actor: str = Field(default="Command Dispatcher", description="Name/role of the officer performing the action")
    notes: Optional[str] = Field(default=None, description="Optional operational notes or verification findings")


class IncidentResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    incident_id: str
    source: IncidentSource
    type: IncidentType
    title: str
    description: str
    severity: IncidentSeverity
    priority: IncidentPriority
    status: IncidentStatus
    location: GeoPoint
    address: str
    reported_at: datetime
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    duplicate_of: Optional[str] = None
    confidence: float = 0.0
    assigned_resources: List[str] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    distance_km: Optional[float] = None

    class Config:
        populate_by_name = True


class IncidentPaginatedResponse(BaseModel):
    items: List[IncidentResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class IncidentStatsResponse(BaseModel):
    total_incidents: int
    active_incidents: int
    critical_incidents: int
    resolved_incidents: int
    closed_incidents: int
    incidents_by_type: Dict[str, int]
    incidents_by_severity: Dict[str, int]
    incidents_by_priority: Dict[str, int]
    incidents_by_status: Dict[str, int]
    incidents_by_source: Dict[str, int]
