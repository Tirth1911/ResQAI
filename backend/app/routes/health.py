from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database, DatabaseManager
from backend.app.config import settings

router = APIRouter()


@router.get("/health", summary="System Health & Database Status")
async def health_check():
    """Verify backend status, MongoDB connectivity, and version info."""
    mongo_healthy = await DatabaseManager.is_healthy()
    return {
        "status": "healthy" if mongo_healthy else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "type": "MongoDB",
            "connected": mongo_healthy,
            "database_name": settings.MONGODB_DB_NAME
        },
        "environment": "development" if settings.DEBUG else "production"
    }
