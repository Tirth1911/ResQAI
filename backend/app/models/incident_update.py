from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class IncidentUpdateModel(BaseModel):
    update_id: str = Field(..., description="Formatted update ID e.g. UPD-7001")
    incident_id: str
    author: str = "Command Officer"
    message: str
    status_change: Optional[str] = None
    resources_changed: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
