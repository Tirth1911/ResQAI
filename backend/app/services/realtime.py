import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from backend.app.websocket.manager import ws_manager, WebSocketEventType

logger = logging.getLogger("resqai.realtime")


def _sanitize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(doc)
    if "_id" in payload and not isinstance(payload["_id"], str):
        payload["_id"] = str(payload["_id"])
    if "id" not in payload and "_id" in payload:
        payload["id"] = payload["_id"]
    return payload


async def broadcast_incident_created(incident_data: Dict[str, Any]) -> None:
    """Broadcast NEW_INCIDENT (and INCIDENT_CREATED) event to all connected clients."""
    inc_id = incident_data.get("incident_id") or str(incident_data.get("_id", "unknown"))
    logger.info(f"[Realtime] Broadcasting NEW_INCIDENT for incident: {inc_id}")
    payload = _sanitize_doc(incident_data)

    event_id = ws_manager.generate_event_id()
    # Broadcast canonical NEW_INCIDENT event
    await ws_manager.broadcast_event(WebSocketEventType.NEW_INCIDENT, payload, event_id=event_id)
    # Broadcast alias INCIDENT_CREATED with same event_id for legacy subscribers
    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_CREATED, payload, event_id=f"{event_id}_alias")


async def broadcast_incident_updated(incident_data: Dict[str, Any]) -> None:
    """Broadcast INCIDENT_UPDATED event to all connected WebSocket clients."""
    inc_id = incident_data.get("incident_id") or str(incident_data.get("_id", "unknown"))
    logger.info(f"[Realtime] Broadcasting INCIDENT_UPDATED for incident: {inc_id}")
    payload = _sanitize_doc(incident_data)
    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, payload)


async def broadcast_incident_resolved(incident_data: Dict[str, Any]) -> None:
    """Broadcast INCIDENT_RESOLVED and INCIDENT_UPDATED events to all connected clients."""
    inc_id = incident_data.get("incident_id") or str(incident_data.get("_id", "unknown"))
    logger.info(f"[Realtime] Broadcasting INCIDENT_RESOLVED for incident: {inc_id}")
    payload = _sanitize_doc(incident_data)
    evt_id = ws_manager.generate_event_id()
    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_RESOLVED, payload, event_id=evt_id)
    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, payload, event_id=f"{evt_id}_upd")


async def broadcast_dispatch_required(
    incident_id: str,
    required_resource_type: Any,
    recommended_resource_ids: List[str],
    priority: str,
    location: Any,
    reason: str,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Broadcast DISPATCH_REQUIRED event when incident necessitates emergency fleet resources."""
    logger.info(f"[Realtime] Broadcasting DISPATCH_REQUIRED for incident: {incident_id}")
    payload = {
        "incident_id": incident_id,
        "required_resource_type": required_resource_type,
        "recommended_resource_ids": recommended_resource_ids,
        "priority": priority,
        "location": location,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **(extra or {})
    }
    await ws_manager.broadcast_event(WebSocketEventType.DISPATCH_REQUIRED, payload)


async def broadcast_resource_dispatched(
    resource_id: str,
    incident_id: str,
    resource_data: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Broadcast RESOURCE_DISPATCHED (and RESOURCE_ASSIGNED) to connected clients."""
    logger.info(f"[Realtime] Broadcasting RESOURCE_DISPATCHED for resource: {resource_id} -> {incident_id}")
    payload = {
        "resource_id": resource_id,
        "incident_id": incident_id,
        "status": "BUSY",
        **(resource_data or {}),
        **(extra or {})
    }
    payload = _sanitize_doc(payload)
    evt_id = ws_manager.generate_event_id()
    await ws_manager.broadcast_event(WebSocketEventType.RESOURCE_DISPATCHED, payload, event_id=evt_id)
    await ws_manager.broadcast_event(WebSocketEventType.RESOURCE_ASSIGNED, payload, event_id=f"{evt_id}_alias")
    await ws_manager.broadcast_event(WebSocketEventType.RESOURCE_UPDATED, payload, event_id=f"{evt_id}_upd")


async def broadcast_resource_available(
    resource_id: str,
    resource_data: Optional[Dict[str, Any]] = None,
    previous_incident_id: Optional[str] = None
) -> None:
    """Broadcast RESOURCE_AVAILABLE (and RESOURCE_RELEASED) to connected clients."""
    logger.info(f"[Realtime] Broadcasting RESOURCE_AVAILABLE for resource: {resource_id}")
    payload = {
        "resource_id": resource_id,
        "status": "AVAILABLE",
        "previous_incident_id": previous_incident_id,
        **(resource_data or {})
    }
    payload = _sanitize_doc(payload)
    evt_id = ws_manager.generate_event_id()
    await ws_manager.broadcast_event(WebSocketEventType.RESOURCE_AVAILABLE, payload, event_id=evt_id)
    await ws_manager.broadcast_event(WebSocketEventType.RESOURCE_RELEASED, payload, event_id=f"{evt_id}_alias")
    await ws_manager.broadcast_event(WebSocketEventType.RESOURCE_UPDATED, payload, event_id=f"{evt_id}_upd")


async def broadcast_resource_assigned(
    incident_id: str,
    resource_data: Dict[str, Any],
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Legacy helper for RESOURCE_ASSIGNED."""
    r_id = resource_data.get("resource_id") or str(resource_data.get("_id", "unknown"))
    await broadcast_resource_dispatched(r_id, incident_id, resource_data, extra)


async def broadcast_incident_escalated(incident_data: Dict[str, Any]) -> None:
    """Broadcast INCIDENT_ESCALATED event to all connected WebSocket clients."""
    inc_id = incident_data.get("incident_id") or str(incident_data.get("_id", "unknown"))
    logger.info(f"[Realtime] Broadcasting INCIDENT_ESCALATED for incident: {inc_id}")
    payload = _sanitize_doc(incident_data)
    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_ESCALATED, payload)


async def broadcast_alert_created(alert_data: Dict[str, Any]) -> None:
    """Broadcast ALERT_CREATED to all connected WebSocket clients."""
    payload = _sanitize_doc(alert_data)
    evt_id = ws_manager.generate_event_id()
    await ws_manager.broadcast_event(WebSocketEventType.ALERT_CREATED, payload, event_id=evt_id)
    await ws_manager.broadcast_event(WebSocketEventType.NOTIFICATION_CREATED, payload, event_id=f"{evt_id}_notif")

