from fastapi import APIRouter
from backend.app.routes.health import router as health_router
from backend.app.routes.incidents import router as incidents_router
from backend.app.routes.resources import router as resources_router
from backend.app.routes.hospitals import router as hospitals_router
from backend.app.routes.alerts import router as alerts_router
from backend.app.routes.notifications import router as notifications_router
from backend.app.routes.analytics import router as analytics_router
from backend.app.routes.simulation import router as simulation_router
from backend.app.routes.auth import router as auth_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(resources_router, prefix="/resources", tags=["Resources"])
api_router.include_router(hospitals_router, prefix="/hospitals", tags=["Hospitals"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(simulation_router, prefix="/simulation", tags=["Simulation"])

__all__ = ["api_router"]

