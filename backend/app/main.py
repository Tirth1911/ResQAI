import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import DatabaseManager
from backend.app.routes import api_router
from backend.app.websocket.manager import ws_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("resqai.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifecycle hooks."""
    logger.info("Starting ResQAI backend service...")
    await DatabaseManager.connect_to_mongo()
    yield
    logger.info("Shutting down ResQAI backend service...")
    await DatabaseManager.close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Emergency Response & Resource Coordination Platform Backend API (MongoDB Datastore)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

from backend.app.routers import incidents_router

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API Ingestion Router under /api and /api/v1
app.include_router(incidents_router, prefix="/api", tags=["Ingestion & Incident API"])
app.include_router(incidents_router, prefix=settings.API_V1_STR, tags=["Ingestion & Incident API"])

# Mount Legacy REST API Routes under /api/v1 and /api
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")



# -----------------------------------------------------------------------------
# WebSocket Real-Time Telemetry & Dashboard Bus
# -----------------------------------------------------------------------------
async def handle_dashboard_websocket(websocket: WebSocket, client_type: str = "dashboard"):
    await ws_manager.connect(websocket)
    try:
        # Send initial handshake packet
        await ws_manager.send_personal_message({
            "event": "CONNECTED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "message": "Connected to ResQAI Real-time Emergency Event Bus",
                "client_type": client_type,
                "server_time": datetime.now(timezone.utc).isoformat()
            }
        }, websocket)

        while True:
            raw_text = await websocket.receive_text()
            if raw_text.strip().lower() in ["ping", '{"type":"ping"}', '{"event":"ping"}']:
                await ws_manager.send_personal_message({
                    "event": "PONG",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": {"status": "alive"}
                }, websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket client stream ended: {e}")
        ws_manager.disconnect(websocket)


@app.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """Primary Real-time WebSocket channel for Command Center Dashboards."""
    await handle_dashboard_websocket(websocket, client_type="dashboard")


@app.websocket("/ws")
async def websocket_alias_endpoint(websocket: WebSocket):
    """Alias route for WebSocket client compatibility."""
    await handle_dashboard_websocket(websocket, client_type="general")


@app.get("/", summary="Root Index")
async def root():
    return {
        "platform": "ResQAI Emergency Response & Resource Coordination",
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
        "api": "/api",
        "database": "MongoDB"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
