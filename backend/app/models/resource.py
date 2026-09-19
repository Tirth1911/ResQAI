from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.models.incident import GeoPoint


class ResourceCategory(str, Enum):
    AMBULANCE = "AMBULANCE"
    FIRE_TRUCK = "FIRE_TRUCK"
    POLICE = "POLICE"
    RESCUE_TEAM = "RESCUE_TEAM"
    MEDICAL_TEAM = "MEDICAL_TEAM"
    DISASTER_TEAM = "DISASTER_TEAM"


class ResourceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    EN_ROUTE = "EN_ROUTE"
    OFFLINE = "OFFLINE"


class ResourceModel(BaseModel):
    resource_id: str = Field(..., description="Formatted resource identifier e.g. RES-2001")
    name: str
    category: ResourceCategory
    capabilities: List[str] = Field(default_factory=list)
    status: ResourceStatus = Field(default=ResourceStatus.AVAILABLE)
    location: GeoPoint
    capacity: int = Field(default=1, ge=1)
    current_incident_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
