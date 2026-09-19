import asyncio
from datetime import datetime, timezone
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import close_client, ensure_indexes, get_client, get_db
from app.routers.incidents import router as incidents_router
from app.services.alerts import run_alert_checks
from app.services.realtime import manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resqai")


async def _alert_monitor_loop() -> None:
    """Periodic background task running delayed response and escalation checks every 30s."""
    logger.info("Alert monitor background service started.")
    while True:
        try:
            await asyncio.sleep(30)
            db = get_db()
            created = await run_alert_checks(db)
            if created:
                logger.info("Background check generated %d alerts.", len(created))
        except asyncio.CancelledError:
            logger.info("Alert monitor background service cancelled.")
            break
        except Exception as exc:
            logger.warning("Error during periodic alert check: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    logger.info("Starting ResQAI API...")
    try:
        client = get_client()
        await client.admin.command("ping")
        logger.info("Successfully pinged MongoDB on startup.")
    except Exception as exc:
        logger.warning("MongoDB ping failed at startup (service may be offline): %s", exc)

    try:
        await ensure_indexes()
        logger.info("Database indexes checked.")
        from app.seed import seed
        await seed()
        logger.info("Database seed checked/applied.")
    except Exception as exc:
        logger.warning("Failed to ensure MongoDB indexes or seed at startup: %s", exc)

    # Start background alert monitor loop
    monitor_task = asyncio.create_task(_alert_monitor_loop())

    yield

    logger.info("Shutting down ResQAI API...")
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass

    await close_client()
    logger.info("MongoDB connection closed.")


app = FastAPI(
    title="ResQAI API",
    lifespan=lifespan,
)

# Configure CORS
origins = list({
    settings.FRONTEND_ORIGIN,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint with real MongoDB ping."""
    db_status = "down"
    try:
        client = get_client()
        await client.admin.command("ping")
        db_status = "up"
    except Exception:
        db_status = "down"
    return {"status": "ok", "db": db_status}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Native WebSocket endpoint streaming real-time emergency events."""
    await manager.connect(websocket)
    try:
        # Initial greeting handshake
        await websocket.send_json({
            "event": "connected",
            "data": {"message": "ResQAI Realtime Gateway Connected"},
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        while True:
            # Keep alive and listen for client messages
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.debug("WebSocket connection terminated: %s", exc)
        manager.disconnect(websocket)
