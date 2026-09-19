import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.schemas.resource import ResourceCreate, ResourceUpdate
from backend.app.models.resource import ResourceStatus, ResourceCategory
from backend.app.utils.geo import create_geojson_point, haversine_distance_km
from backend.app.websocket.manager import ws_manager

logger = logging.getLogger("resqai.services.resource")


class ResourceService:
    @staticmethod
    def _format_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    @classmethod
    async def create_resource(cls, db: AsyncIOMotorDatabase, data: ResourceCreate) -> Dict[str, Any]:
        """Create new emergency response resource in MongoDB."""
        now = datetime.utcnow()
        doc = {
            "resource_id": data.resource_id,
            "name": data.name,
            "category": data.category.value if hasattr(data.category, "value") else data.category,
            "capabilities": data.capabilities,
            "status": data.status.value if hasattr(data.status, "value") else data.status,
            "capacity": data.capacity,
            "current_incident_id": data.current_incident_id,
            "location": create_geojson_point(data.location.latitude, data.location.longitude),
            "updated_at": now,
        }
        res = await db.resources.insert_one(doc)
        doc["_id"] = str(res.inserted_id)

        await ws_manager.broadcast({
            "event": "RESOURCE_CREATED",
            "data": doc
        })
        return doc

    @classmethod
    async def list_resources(
        cls,
        db: AsyncIOMotorDatabase,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if category:
            query["category"] = category

        cursor = db.resources.find(query).limit(limit)
        results = []
        async for doc in cursor:
            results.append(cls._format_doc(doc))
        return results

    @classmethod
    async def get_nearest_available_resources(
        cls,
        db: AsyncIOMotorDatabase,
        lat: float,
        lon: float,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find closest AVAILABLE resources to a target coordinate."""
        query: Dict[str, Any] = {"status": ResourceStatus.AVAILABLE.value}
        if category:
            query["category"] = category

        cursor = db.resources.find(query)
        candidates = []
        async for doc in cursor:
            coords = doc.get("location", {}).get("coordinates", [])
            if len(coords) == 2:
                r_lon, r_lat = coords[0], coords[1]
                distance = haversine_distance_km(lat, lon, r_lat, r_lon)
                doc_formatted = cls._format_doc(doc)
                doc_formatted["distance_km"] = round(distance, 2)
                candidates.append(doc_formatted)

        # Sort by distance
        candidates.sort(key=lambda x: x["distance_km"])
        return candidates[:limit]

    @classmethod
    async def update_resource_status(
        cls,
        db: AsyncIOMotorDatabase,
        resource_id: str,
        status: ResourceStatus,
        current_incident_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update responder status and broadcast change."""
        try:
            now = datetime.utcnow()
            update_fields: Dict[str, Any] = {
                "status": status.value if hasattr(status, "value") else status,
                "updated_at": now
            }
            if current_incident_id is not None:
                update_fields["current_incident_id"] = current_incident_id

            query = {"resource_id": resource_id}
            if ObjectId.is_valid(resource_id):
                query = {"$or": [{"resource_id": resource_id}, {"_id": ObjectId(resource_id)}]}

            await db.resources.update_one(query, {"$set": update_fields})
            updated = await db.resources.find_one(query)
            if updated:
                formatted = cls._format_doc(updated)
                await ws_manager.broadcast({
                    "event": "RESOURCE_UPDATED",
                    "data": formatted
                })
                return formatted
            return None
        except Exception as e:
            logger.error(f"Failed to update resource status: {e}")
            return None
