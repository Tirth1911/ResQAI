import json
import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger("resqai.realtime")


class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasts event envelopes.
    Envelope format: {"event": "<name>", "data": {...}, "ts": "<ISO8601>"}
    """

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts and tracks a newly opened WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected. Active connections: %d",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Removes a closed or disconnected WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                "WebSocket client disconnected. Active connections: %d",
                len(self.active_connections),
            )

    async def broadcast(self, event: str, data: dict[str, Any]) -> None:
        """
        Broadcasts a typed event envelope to all connected WebSocket clients.
        Safely removes any broken/dead connections without interrupting callers.
        """
        envelope = {
            "event": event,
            "data": data,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        message_text = json.dumps(envelope)

        disconnected: list[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message_text)
            except Exception as exc:
                logger.debug("Failed sending to WebSocket, marking for removal: %s", exc)
                disconnected.append(connection)

        for dead_conn in disconnected:
            self.disconnect(dead_conn)


# Global singleton instance
manager = ConnectionManager()


async def broadcast(event: str, data: dict[str, Any]) -> None:
    """Convenience module-level broadcaster."""
    await manager.broadcast(event, data)
