from typing import Optional
from pydantic import BaseModel, Field
from backend.app.models.hospital import HospitalStatus
from backend.app.models.incident import GeoPoint
from backend.app.schemas.incident import IncidentLocationInput


class HospitalCreate(BaseModel):
    hospital_id: Optional[str] = None
    name: str
    location: IncidentLocationInput
    beds_available: int = 0
    icu_available: int = 0
    emergency_capacity: int = 0
    status: HospitalStatus = HospitalStatus.OPEN


class HospitalResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    hospital_id: str
    name: str
    location: GeoPoint
    beds_available: int
    icu_available: int
    emergency_capacity: int
    status: HospitalStatus
    distance_km: Optional[float] = None

    class Config:
        populate_by_name = True
