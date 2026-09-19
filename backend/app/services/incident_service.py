import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.schemas.incident import IncidentCreate, IncidentUpdate
from backend.app.models.incident import IncidentStatus, IncidentSource, IncidentType
from backend.app.utils.geo import create_geojson_point
from backend.app.ai.triage import AITriageEngine
from backend.app.services.dedup_service import DeduplicationService
from backend.app.websocket.manager import ws_manager

logger = logging.getLogger("resqai.services.incident")


class IncidentService:
    @staticmethod
    def _format_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string _id."""
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    @classmethod
    async def create_incident(
        cls,
        db: AsyncIOMotorDatabase,
        data: IncidentCreate,
        auto_dedup: bool = True
    ) -> Dict[str, Any]:
        """Create or merge incident, triage using AI, store in MongoDB, and broadcast via WebSockets."""
        lat = data.location.latitude
        lon = data.location.longitude

        # Check for duplicate active incidents
        if auto_dedup:
            duplicate = await DeduplicationService.find_duplicate_incident(
                db=db,
                lat=lat,
                lon=lon,
                incident_type=data.type.value if hasattr(data.type, "value") else str(data.type)
            )
            if duplicate:
                # Merge into existing incident
                dup_id = duplicate["_id"]
                now = datetime.utcnow()
                
                await db.incidents.update_one(
                    {"_id": dup_id},
                    {
                        "$set": {"updated_at": now},
                        "$push": {
                            "timeline": {
                                "timestamp": now,
                                "action": "Duplicate Call Merged",
                                "actor": data.source.value if hasattr(data.source, "value") else str(data.source),
                                "details": f"Duplicate report merged: {data.title}"
                            }
                        }
                    }
                )
                
                updated_inc = await db.incidents.find_one({"_id": dup_id})
                result = cls._format_doc(updated_inc)
                
                # Broadcast real-time update
                await ws_manager.broadcast({
                    "event": "INCIDENT_DUPLICATE_MERGED",
                    "data": result,
                    "merged_report": {"title": data.title, "description": data.description}
                })
                return result

        # Run AI Triage if not fully specified
        ai_triage = data.ai_analysis or AITriageEngine.classify_text(f"{data.title} {data.description}")

        now = datetime.utcnow()
        random_suffix = uuid.uuid4().hex[:4].upper()
        incident_id = data.incident_id or f"INC-{random_suffix}"

        doc = {
            "incident_id": incident_id,
            "source": data.source.value if hasattr(data.source, "value") else str(data.source),
            "type": data.type.value if hasattr(data.type, "value") else str(data.type),
            "title": data.title,
            "description": data.description,
            "severity": data.severity.value if hasattr(data.severity, "value") else str(data.severity),
            "priority": data.priority.value if hasattr(data.priority, "value") else str(data.priority),
            "status": data.status.value if hasattr(data.status, "value") else str(data.status),
            "location": create_geojson_point(lat, lon),
            "address": data.address or data.location.address or f"Lat: {lat}, Lon: {lon}",
            "reported_at": now,
            "updated_at": now,
            "ai_analysis": ai_triage,
            "duplicate_of": data.duplicate_of,
            "confidence": data.confidence or ai_triage.get("confidence", 0.9),
            "assigned_resources": data.assigned_resources,
            "timeline": [{
                "timestamp": now,
                "action": "Incident Reported",
                "actor": data.source.value if hasattr(data.source, "value") else str(data.source),
                "details": f"Initial report logged: {data.title}"
            }]
        }

        res = await db.incidents.insert_one(doc)
        doc["_id"] = str(res.inserted_id)

        # Broadcast real-time incident event
        await ws_manager.broadcast({
            "event": "INCIDENT_CREATED",
            "data": doc
        })

        return doc

    @classmethod
    async def list_incidents(
        cls,
        db: AsyncIOMotorDatabase,
        status: Optional[str] = None,
        incident_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List incidents with filtering."""
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if incident_type:
            query["type"] = incident_type
        if severity:
            query["severity"] = severity

        cursor = db.incidents.find(query).sort("reported_at", -1).skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            results.append(cls._format_doc(doc))
        return results

    @classmethod
    async def get_incident(cls, db: AsyncIOMotorDatabase, incident_id: str) -> Optional[Dict[str, Any]]:
        """Fetch incident by incident_id or ObjectId."""
        try:
            doc = await db.incidents.find_one({"incident_id": incident_id})
            if not doc and ObjectId.is_valid(incident_id):
                doc = await db.incidents.find_one({"_id": ObjectId(incident_id)})
            return cls._format_doc(doc) if doc else None
        except Exception:
            return None

    @classmethod
    async def update_incident(
        cls,
        db: AsyncIOMotorDatabase,
        incident_id: str,
        data: IncidentUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update incident attributes and broadcast change."""
        try:
            update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
            if not update_data:
                return await cls.get_incident(db, incident_id)

            update_data["updated_at"] = datetime.utcnow()
            
            # Enum conversion to value
            for k in ["source", "type", "severity", "priority", "status"]:
                if k in update_data and hasattr(update_data[k], "value"):
                    update_data[k] = update_data[k].value

            query = {"incident_id": incident_id}
            if ObjectId.is_valid(incident_id):
                query = {"$or": [{"incident_id": incident_id}, {"_id": ObjectId(incident_id)}]}

            await db.incidents.update_one(
                query,
                {"$set": update_data}
            )
            updated = await cls.get_incident(db, incident_id)
            if updated:
                await ws_manager.broadcast({
                    "event": "INCIDENT_UPDATED",
                    "data": updated
                })
            return updated
        except Exception as e:
            logger.error(f"Error updating incident: {e}")
            return None
