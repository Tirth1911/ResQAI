from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.config import settings
from backend.app.utils.geo import haversine_distance_km


class DeduplicationService:
    @staticmethod
    async def find_duplicate_incident(
        db: AsyncIOMotorDatabase,
        lat: float,
        lon: float,
        incident_type: str,
        threshold_km: float = settings.DEDUP_DISTANCE_THRESHOLD_KM,
        time_window_minutes: int = settings.DEDUP_TIME_WINDOW_MINUTES
    ) -> Optional[Dict[str, Any]]:
        """
        Check if an active incident of matching/compatible type exists within
        the given distance threshold (km) and time window (minutes).
        Uses MongoDB geospatial index ($near or $geoWithin) or bounding query.
        """
        time_cutoff = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        # Query active incidents created recently
        cursor = db.incidents.find({
            "status": {"$in": ["REPORTED", "TRIAGED", "DISPATCHED", "IN_PROGRESS"]},
            "created_at": {"$gte": time_cutoff}
        })

        async for inc in cursor:
            # Check spatial distance
            coords = inc.get("location", {}).get("coordinates", [])
            if len(coords) == 2:
                inc_lon, inc_lat = coords[0], coords[1]
                dist = haversine_distance_km(lat, lon, inc_lat, inc_lon)
                
                # If within radius and incident type matches or is 'Other'
                if dist <= threshold_km:
                    if inc.get("incident_type") == incident_type or incident_type == "Other" or inc.get("incident_type") == "Other":
                        return inc

        return None
