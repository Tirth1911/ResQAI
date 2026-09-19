from typing import Dict, List, Any
from pydantic import BaseModel


class SystemStats(BaseModel):
    total_incidents: int
    active_incidents: int
    resolved_incidents: int
    critical_incidents: int
    total_resources: int
    available_resources: int
    dispatched_resources: int
    incidents_by_type: Dict[str, int]
    incidents_by_severity: Dict[str, int]
    incidents_by_priority: Dict[str, int]
