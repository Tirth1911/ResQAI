from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.models.resource import ResourceCategory, ResourceStatus
from backend.app.models.incident import GeoPoint
from backend.app.schemas.incident import IncidentLocationInput


class ResourceCreate(BaseModel):
    resource_id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=100)
    category: ResourceCategory
    capabilities: List[str] = Field(default_factory=list)
    status: ResourceStatus = Field(default=ResourceStatus.AVAILABLE)
    location: IncidentLocationInput
    capacity: int = Field(default=1, ge=1)
    current_incident_id: Optional[str] = None


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[ResourceCategory] = None
    capabilities: Optional[List[str]] = None
    status: Optional[ResourceStatus] = None
    location: Optional[IncidentLocationInput] = None
    capacity: Optional[int] = None
    current_incident_id: Optional[str] = None


class ResourceResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    resource_id: str
    name: str
    category: ResourceCategory
    capabilities: List[str] = Field(default_factory=list)
    status: ResourceStatus
    location: GeoPoint
    capacity: int
    current_incident_id: Optional[str] = None
    updated_at: datetime
    distance_km: Optional[float] = None

    class Config:
        populate_by_name = True
