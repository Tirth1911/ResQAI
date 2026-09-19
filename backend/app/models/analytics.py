from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AnalyticsSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_incidents: int = 0
    active_incidents: int = 0
    resolved_incidents: int = 0
    critical_incidents: int = 0
    resources_available: int = 0
    resources_busy: int = 0
    incidents_by_type: Dict[str, int] = Field(default_factory=dict)
    incidents_by_severity: Dict[str, int] = Field(default_factory=dict)
