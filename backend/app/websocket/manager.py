import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from fastapi import WebSocket

logger = logging.getLogger("resqai.websocket")


class WebSocketEventType(str, Enum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_UPDATED = "INCIDENT_UPDATED"
    INCIDENT_CLASSIFIED = "INCIDENT_CLASSIFIED"
    INCIDENT_DUPLICATED = "INCIDENT_DUPLICATED"
    RESOURCE_ASSIGNED = "RESOURCE_ASSIGNED"
    RESOURCE_RELEASED = "RESOURCE_RELEASED"
    INCIDENT_ESCALATED = "INCIDENT_ESCALATED"
    RESOURCE_SHORTAGE = "RESOURCE_SHORTAGE"
    ALERT_CREATED = "alert_created"
    NOTIFICATION_CREATED = "NOTIFICATION_CREATED"
    HEARTBEAT_PONG = "PONG"


class ConnectionManager:
    """
    In-memory WebSocket Connection Manager for ResQAI real-time dashboard clients.
    Thread-safe and async-safe with automatic stale client cleanup and JSON serialization.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

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

    async def broadcast_event(self, event: str, data: Dict[str, Any]):
        """
        Broadcast standardized event envelope to all connected dashboard clients.
        Envelope Format:
        {
            "event": "INCIDENT_CREATED",
            "timestamp": "2026-09-19T13:45:00.000Z",
            "data": { ... }
        }
        """
        message = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        await self.broadcast(message)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast raw dictionary or standardized message to all clients."""
        if not self.active_connections:
            return

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
