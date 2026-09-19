import logging
from typing import Dict, Any

logger = logging.getLogger("resqai.realtime")


async def broadcast_incident_created(incident_data: Dict[str, Any]) -> None:
    """Stub broadcast function for incident_created event."""
    inc_id = incident_data.get("incident_id") or incident_data.get("_id", "unknown")
    logger.info(f"[Realtime Stub] Broadcast incident_created for incident: {inc_id}")
