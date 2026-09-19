import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import close_client, ensure_indexes, get_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resqai")


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
    except Exception as exc:
        logger.warning("Failed to ensure MongoDB indexes at startup: %s", exc)

    yield

    logger.info("Shutting down ResQAI API...")
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
