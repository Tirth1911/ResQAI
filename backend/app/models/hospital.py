from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from backend.app.models.incident import GeoPoint


class HospitalStatus(str, Enum):
    OPEN = "OPEN"
    LIMITED = "LIMITED"
    CLOSED = "CLOSED"


class HospitalModel(BaseModel):
    hospital_id: str = Field(..., description="Formatted hospital identifier e.g. HOS-4001")
    name: str
    location: GeoPoint
    beds_available: int = Field(default=0, ge=0)
    icu_available: int = Field(default=0, ge=0)
    emergency_capacity: int = Field(default=0, ge=0)
    status: HospitalStatus = Field(default=HospitalStatus.OPEN)
