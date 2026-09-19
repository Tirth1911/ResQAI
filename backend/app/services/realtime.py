import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("resqai.realtime")


async def broadcast(event: str, data: dict[str, Any]) -> None:
    """
    Broadcasts real-time events to connected WebSocket clients.
    Stub implementation for Step 3; native WebSocket connection manager will be hooked in Step 6.
    """
    envelope = {
        "event": event,
        "data": data,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    logger.debug("Broadcast event '%s': %s", event, envelope)
