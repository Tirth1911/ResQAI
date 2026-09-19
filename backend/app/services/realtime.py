import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from backend.app.websocket.manager import ws_manager, WebSocketEventType

logger = logging.getLogger("resqai.realtime")


async def broadcast_incident_created(incident_data: Dict[str, Any]) -> None:
    """Broadcast INCIDENT_CREATED event to all connected WebSocket clients."""
    inc_id = incident_data.get("incident_id") or str(incident_data.get("_id", "unknown"))
    logger.info(f"[Realtime] Broadcasting INCIDENT_CREATED for incident: {inc_id}")

    # Ensure _id is serialisable
    payload = dict(incident_data)
    if "_id" in payload and not isinstance(payload["_id"], str):
        payload["_id"] = str(payload["_id"])
    if "id" not in payload and "_id" in payload:
        payload["id"] = payload["_id"]

    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_CREATED, payload)


async def broadcast_incident_updated(incident_data: Dict[str, Any]) -> None:
    """Broadcast INCIDENT_UPDATED event to all connected WebSocket clients."""
    inc_id = incident_data.get("incident_id") or str(incident_data.get("_id", "unknown"))
    logger.info(f"[Realtime] Broadcasting INCIDENT_UPDATED for incident: {inc_id}")

    payload = dict(incident_data)
    if "_id" in payload and not isinstance(payload["_id"], str):
        payload["_id"] = str(payload["_id"])
    if "id" not in payload and "_id" in payload:
        payload["id"] = payload["_id"]

    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, payload)


async def broadcast_resource_assigned(
    incident_id: str,
    resource_data: Dict[str, Any],
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Broadcast RESOURCE_ASSIGNED event to all connected WebSocket clients."""
    logger.info(f"[Realtime] Broadcasting RESOURCE_ASSIGNED for incident: {incident_id}")

    payload = {
        "incident_id": incident_id,
        "resource_id": resource_data.get("resource_id") or str(resource_data.get("_id", "unknown")),
        "resource_name": resource_data.get("name") or resource_data.get("resource_name"),
        "kind": resource_data.get("kind") or resource_data.get("category"),
        **(extra or {})
    }
    await ws_manager.broadcast_event(WebSocketEventType.RESOURCE_ASSIGNED, payload)


async def broadcast_incident_escalated(incident_data: Dict[str, Any]) -> None:
    """Broadcast INCIDENT_ESCALATED event to all connected WebSocket clients."""
    inc_id = incident_data.get("incident_id") or str(incident_data.get("_id", "unknown"))
    logger.info(f"[Realtime] Broadcasting INCIDENT_ESCALATED for incident: {inc_id}")

    payload = dict(incident_data)
    if "_id" in payload and not isinstance(payload["_id"], str):
        payload["_id"] = str(payload["_id"])
    if "id" not in payload and "_id" in payload:
        payload["id"] = payload["_id"]

    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_ESCALATED, payload)
