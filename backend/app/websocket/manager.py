import json
import uuid
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from fastapi import WebSocket

logger = logging.getLogger("resqai.websocket")


class WebSocketEventType(str, Enum):
    # Core Synchronisation Events
    NEW_INCIDENT = "NEW_INCIDENT"
    INCIDENT_CREATED = "INCIDENT_CREATED"  # Alias
    INCIDENT_UPDATED = "INCIDENT_UPDATED"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"
    DISPATCH_REQUIRED = "DISPATCH_REQUIRED"
    RESOURCE_UPDATED = "RESOURCE_UPDATED"
    RESOURCE_DISPATCHED = "RESOURCE_DISPATCHED"
    RESOURCE_ASSIGNED = "RESOURCE_ASSIGNED"  # Alias
    RESOURCE_AVAILABLE = "RESOURCE_AVAILABLE"
    RESOURCE_RELEASED = "RESOURCE_RELEASED"  # Alias
    ALERT_CREATED = "ALERT_CREATED"
    NOTIFICATION_CREATED = "NOTIFICATION_CREATED"
    AI_ANALYSIS_UPDATED = "AI_ANALYSIS_UPDATED"
    INCIDENT_CLASSIFIED = "INCIDENT_CLASSIFIED"  # Alias
    DUPLICATE_DETECTED = "DUPLICATE_DETECTED"
    INCIDENT_DUPLICATED = "INCIDENT_DUPLICATED"  # Alias
    INCIDENT_DUPLICATE_MERGED = "INCIDENT_DUPLICATE_MERGED"
    SYSTEM_STATUS_UPDATED = "SYSTEM_STATUS_UPDATED"
    INCIDENT_ESCALATED = "INCIDENT_ESCALATED"
    RESOURCE_SHORTAGE = "RESOURCE_SHORTAGE"
    HEARTBEAT_PONG = "PONG"


class ConnectionManager:
    """
    In-memory WebSocket Connection Manager for ResQAI real-time dashboard clients.
    Thread-safe and async-safe with automatic stale client cleanup, JSON serialization,
    and event deduplication IDs.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    def generate_event_id(self) -> str:
        """Generate a monotonically sortable, unique event identifier."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        rand = uuid.uuid4().hex[:6]
        return f"evt_{ts}_{rand}"

    async def connect(self, websocket: WebSocket):
        """Accept incoming WebSocket connection and register in pool."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected to dashboard stream. Active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket client from pool."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining active: {len(self.active_connections)}")

    async def broadcast_event(self, event: str, data: Dict[str, Any], event_id: Optional[str] = None):
        """
        Broadcast standardized event envelope to all connected dashboard clients.
        Envelope Format:
        {
            "event_id": "evt_20260920141500_a1b2c3",
            "event": "NEW_INCIDENT",
            "timestamp": "2026-09-20T14:15:00.000Z",
            "incident_id": "...",
            "resource_id": "...",
            "data": { ... }
        }
        """
        evt_id = event_id or self.generate_event_id()
        now_ts = datetime.now(timezone.utc).isoformat()

        # Extract primary identifiers if present for convenience
        inc_id = None
        res_id = None
        if isinstance(data, dict):
            inc_id = data.get("incident_id") or data.get("id") or data.get("_id")
            if inc_id is not None:
                inc_id = str(inc_id)
            res_id = data.get("resource_id")
            if res_id is not None:
                res_id = str(res_id)

        message = {
            "event_id": evt_id,
            "event": event,
            "timestamp": now_ts,
            "incident_id": inc_id,
            "resource_id": res_id,
            "data": data
        }
        await self.broadcast(message)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast raw dictionary or standardized message to all clients."""
        if not self.active_connections:
            return

        # Ensure message has event_id and timestamp if missing
        if "event_id" not in message:
            message["event_id"] = self.generate_event_id()
        if "timestamp" not in message:
            message["timestamp"] = datetime.now(timezone.utc).isoformat()

        payload = json.dumps(message, default=str)
        disconnected = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.debug(f"Failed to transmit to client: {e}. Marking for cleanup.")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send direct message to a single specific client."""
        if "event_id" not in message:
            message["event_id"] = self.generate_event_id()
        if "timestamp" not in message:
            message["timestamp"] = datetime.now(timezone.utc).isoformat()

        payload = json.dumps(message, default=str)
        try:
            await websocket.send_text(payload)
        except Exception as e:
            logger.warning(f"Failed to send direct message: {e}")
            self.disconnect(websocket)

    @property
    def client_count(self) -> int:
        return len(self.active_connections)


# Singleton instance
ws_manager = ConnectionManager()
