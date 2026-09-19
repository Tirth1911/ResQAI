from backend.app.routers.incidents import router as incidents_router
from backend.app.routers.alerts import router as alerts_router
from backend.app.routers.analytics import router as analytics_router

__all__ = ["incidents_router", "alerts_router", "analytics_router"]

