from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.models.incident import GeoPoint


class TeamStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"


class TeamMember(BaseModel):
    member_id: str
    name: str
    role: str
    contact: Optional[str] = None


class TeamModel(BaseModel):
    team_id: str = Field(..., description="Formatted team identifier e.g. TEAM-3001")
    name: str
    type: str
    members: List[TeamMember] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    status: TeamStatus = Field(default=TeamStatus.AVAILABLE)
    location: GeoPoint
