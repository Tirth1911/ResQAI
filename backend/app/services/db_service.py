import re
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union, Tuple
from collections import defaultdict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.models import (
    IncidentModel,
    IncidentStatus,
    IncidentSeverity,
    IncidentPriority,
    IncidentType,
    IncidentSource,
    ResourceModel,
    ResourceStatus,
    HospitalModel,
    NotificationModel,
    IncidentUpdateModel,
    GeoPoint,
)
from backend.app.utils.geo import haversine_distance_km
from backend.app.utils.incident_id import generate_incident_id
from backend.app.ai.triage import AITriageEngine

logger = logging.getLogger("resqai.db_service")


def clean_mongo_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Convert ObjectId to string for JSON and Pydantic compatibility."""
    if not doc:
        return None
    doc_copy = dict(doc)
    if "_id" in doc_copy:
        doc_copy["_id"] = str(doc_copy["_id"])
    return doc_copy


def clean_mongo_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [clean_mongo_doc(d) for d in docs if d is not None]


class DBService:
    # -------------------------------------------------------------------------
    # INCIDENTS
    # -------------------------------------------------------------------------

    @staticmethod
    async def create_incident(db: AsyncIOMotorDatabase, incident_data: Union[IncidentModel, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Insert a new emergency incident document into MongoDB.
        If type, severity, or priority are missing, executes AI classification and preparation.
        Assigns a unique human-readable identifier (e.g. INC-20260919-0001).
        """
        if isinstance(incident_data, IncidentModel):
            doc = incident_data.model_dump()
        else:
            doc = dict(incident_data)

        # 1. Human-readable unique incident_id: INC-YYYYMMDD-XXXX
        if "incident_id" not in doc or not doc["incident_id"]:
            doc["incident_id"] = await generate_incident_id(db)

        # 2. Timestamps in UTC
        now_utc = datetime.now(timezone.utc)
        if "reported_at" not in doc or not doc["reported_at"]:
            doc["reported_at"] = now_utc
        if "updated_at" not in doc or not doc["updated_at"]:
            doc["updated_at"] = now_utc

        # 3. AI Analysis & Triage (if type, severity, or priority are omitted or needed)
        title = doc.get("title", "")
        desc = doc.get("description", "")
        text_content = f"{title} {desc}"

        needs_ai_type = not doc.get("type") or doc.get("type") == IncidentType.OTHER or doc.get("type") == "other"
        needs_ai_severity = not doc.get("severity")
        needs_ai_priority = not doc.get("priority")

        if needs_ai_type or needs_ai_severity or needs_ai_priority or not doc.get("ai_analysis"):
            ai_result = AITriageEngine.classify_text(text_content)
            ai_recs = AITriageEngine.generate_recommendations(ai_result["incident_type"], ai_result["severity"])
            
            ai_analysis_dict = {
                "confidence": ai_result.get("confidence", 0.92),
                "suggested_type": ai_result["incident_type"].value,
                "suggested_severity": ai_result["severity"].value,
                "suggested_priority": ai_result["priority"].value,
                "extracted_entities": ai_result.get("extracted_entities", {}),
                "recommended_actions": ai_recs,
                "triaged_at": now_utc.isoformat()
            }

            if not doc.get("type"):
                doc["type"] = ai_result["incident_type"].value
            elif hasattr(doc["type"], "value"):
                doc["type"] = doc["type"].value

            if not doc.get("severity"):
                doc["severity"] = ai_result["severity"].value
            elif hasattr(doc["severity"], "value"):
                doc["severity"] = doc["severity"].value

            if not doc.get("priority"):
                doc["priority"] = ai_result["priority"].value
            elif hasattr(doc["priority"], "value"):
                doc["priority"] = doc["priority"].value

            if not doc.get("confidence"):
                doc["confidence"] = ai_result.get("confidence", 0.92)

            doc["ai_analysis"] = ai_analysis_dict
        else:
            # Ensure enum values are serialized to strings
            for k in ["source", "type", "severity", "priority", "status"]:
                if k in doc and hasattr(doc[k], "value"):
                    doc[k] = doc[k].value

        if "status" not in doc or not doc["status"]:
            doc["status"] = IncidentStatus.REPORTED.value
        elif hasattr(doc["status"], "value"):
            doc["status"] = doc["status"].value

        # 4. Initial Timeline
        if "timeline" not in doc or not doc["timeline"]:
            doc["timeline"] = [{
                "timestamp": now_utc,
                "action": "Incident Reported",
                "actor": doc.get("source", "citizen"),
                "details": f"Initial report logged: {doc.get('title', '')}"
            }]

        res = await db.incidents.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    @staticmethod
    async def get_incident(db: AsyncIOMotorDatabase, incident_id_or_object_id: str) -> Optional[Dict[str, Any]]:
        """Fetch incident by custom incident_id ('INC-YYYYMMDD-XXXX') or MongoDB ObjectId."""
        query: Dict[str, Any] = {"incident_id": incident_id_or_object_id}
        doc = await db.incidents.find_one(query)
        if not doc and ObjectId.is_valid(incident_id_or_object_id):
            doc = await db.incidents.find_one({"_id": ObjectId(incident_id_or_object_id)})
        return clean_mongo_doc(doc)

    @staticmethod
    async def list_incidents(
        db: AsyncIOMotorDatabase,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        priority: Optional[str] = None,
        incident_type: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List incidents with full filtering (type, severity, priority, status, source, date range, search)
        and pagination. Returns (items, total_count).
        """
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity
        if priority:
            query["priority"] = priority
        if incident_type:
            query["type"] = incident_type
        if source:
            query["source"] = source

        # Date Range filter on reported_at
        if start_date or end_date:
            date_filter: Dict[str, Any] = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["reported_at"] = date_filter

        # Keyword search (escaped to prevent regex injection and ReDoS)
        if search and search.strip():
            escaped_search = re.escape(search.strip())
            regex = {"$regex": escaped_search, "$options": "i"}
            query["$or"] = [
                {"title": regex},
                {"description": regex},
                {"address": regex},
                {"incident_id": regex}
            ]

        total = await db.incidents.count_documents(query)
        skip = (max(1, page) - 1) * limit
        cursor = db.incidents.find(query).sort("reported_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return clean_mongo_docs(docs), total

    @staticmethod
    async def get_active_incidents(db: AsyncIOMotorDatabase, page: int = 1, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """Get all currently active incidents (REPORTED, VERIFIED, DISPATCHED, IN_PROGRESS)."""
        query = {"status": {"$in": ["REPORTED", "VERIFIED", "DISPATCHED", "IN_PROGRESS"]}}
        total = await db.incidents.count_documents(query)
        skip = (max(1, page) - 1) * limit
        cursor = db.incidents.find(query).sort("reported_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return clean_mongo_docs(docs), total

    @staticmethod
    async def get_critical_incidents(db: AsyncIOMotorDatabase, page: int = 1, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """Get all critical incidents (severity CRITICAL or priority P1)."""
        query = {
            "$or": [
                {"severity": "CRITICAL"},
                {"priority": "P1"}
            ]
        }
        total = await db.incidents.count_documents(query)
        skip = (max(1, page) - 1) * limit
        cursor = db.incidents.find(query).sort("reported_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return clean_mongo_docs(docs), total

    @staticmethod
    async def update_incident(
        db: AsyncIOMotorDatabase,
        incident_id: str,
        update_data: Dict[str, Any],
        actor: str = "Command Officer"
    ) -> Optional[Dict[str, Any]]:
        """Update incident fields and append an event to the timeline."""
        query = {"incident_id": incident_id}
        existing = await db.incidents.find_one(query)
        if not existing and ObjectId.is_valid(incident_id):
            query = {"_id": ObjectId(incident_id)}
            existing = await db.incidents.find_one(query)

        if not existing:
            return None

        update_fields = {k: v for k, v in update_data.items() if k not in ["_id", "incident_id", "timeline"]}
        update_fields["updated_at"] = datetime.now(timezone.utc)

        # Build timeline event if significant update occurred
        timeline_entry = {
            "timestamp": datetime.now(timezone.utc),
            "action": f"Incident Updated: {', '.join(update_fields.keys())}",
            "actor": actor,
            "details": f"Fields modified: {list(update_fields.keys())}"
        }

        await db.incidents.update_one(
            query,
            {
                "$set": update_fields,
                "$push": {"timeline": timeline_entry}
            }
        )
        updated_doc = await db.incidents.find_one(query)
        return clean_mongo_doc(updated_doc)

    @staticmethod
    async def transition_incident_status(
        db: AsyncIOMotorDatabase,
        incident_id: str,
        new_status: str,
        action_name: str,
        actor: str = "Command Dispatcher",
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute status transition with timestamp and timeline log."""
        query = {"incident_id": incident_id}
        existing = await db.incidents.find_one(query)
        if not existing and ObjectId.is_valid(incident_id):
            query = {"_id": ObjectId(incident_id)}
            existing = await db.incidents.find_one(query)

        if not existing:
            return None

        now_utc = datetime.now(timezone.utc)
        timeline_entry = {
            "timestamp": now_utc,
            "action": action_name,
            "actor": actor,
            "details": notes or f"Status changed from {existing.get('status')} to {new_status}"
        }

        await db.incidents.update_one(
            query,
            {
                "$set": {
                    "status": new_status,
                    "updated_at": now_utc
                },
                "$push": {"timeline": timeline_entry}
            }
        )
        updated_doc = await db.incidents.find_one(query)
        return clean_mongo_doc(updated_doc)

    @staticmethod
    async def delete_incident(db: AsyncIOMotorDatabase, incident_id: str) -> bool:
        """Delete incident document from MongoDB."""
        query = {"incident_id": incident_id}
        if ObjectId.is_valid(incident_id):
            res = await db.incidents.delete_one({"$or": [{"incident_id": incident_id}, {"_id": ObjectId(incident_id)}]})
        else:
            res = await db.incidents.delete_one(query)
        return res.deleted_count > 0

    @staticmethod
    async def find_nearby_incidents(
        db: AsyncIOMotorDatabase,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 10000.0,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find incidents near a target coordinate using MongoDB $near 2dsphere geospatial index.
        """
        query: Dict[str, Any] = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "$maxDistance": max_distance_meters
                }
            }
        }
        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity

        cursor = db.incidents.find(query).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        results = []
        for doc in docs:
            c = clean_mongo_doc(doc)
            coords = c.get("location", {}).get("coordinates", [])
            if len(coords) == 2:
                c["distance_km"] = round(haversine_distance_km(latitude, longitude, coords[1], coords[0]), 2)
            results.append(c)
        return results

    @staticmethod
    async def get_incident_stats(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """Aggregate statistical breakdowns across all emergency incidents."""
        total_incidents = await db.incidents.count_documents({})
        active_incidents = await db.incidents.count_documents({
            "status": {"$in": ["REPORTED", "VERIFIED", "DISPATCHED", "IN_PROGRESS"]}
        })
        critical_incidents = await db.incidents.count_documents({
            "$or": [{"severity": "CRITICAL"}, {"priority": "P1"}]
        })
        resolved_incidents = await db.incidents.count_documents({"status": "RESOLVED"})
        closed_incidents = await db.incidents.count_documents({"status": "CLOSED"})

        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        by_priority = defaultdict(int)
        by_status = defaultdict(int)
        by_source = defaultdict(int)

        async for inc in db.incidents.find({}, {"type": 1, "severity": 1, "priority": 1, "status": 1, "source": 1}):
            if "type" in inc and inc["type"]:
                by_type[str(inc["type"])] += 1
            if "severity" in inc and inc["severity"]:
                by_severity[str(inc["severity"])] += 1
            if "priority" in inc and inc["priority"]:
                by_priority[str(inc["priority"])] += 1
            if "status" in inc and inc["status"]:
                by_status[str(inc["status"])] += 1
            if "source" in inc and inc["source"]:
                by_source[str(inc["source"])] += 1

        return {
            "total_incidents": total_incidents,
            "active_incidents": active_incidents,
            "critical_incidents": critical_incidents,
            "resolved_incidents": resolved_incidents,
            "closed_incidents": closed_incidents,
            "incidents_by_type": dict(by_type),
            "incidents_by_severity": dict(by_severity),
            "incidents_by_priority": dict(by_priority),
            "incidents_by_status": dict(by_status),
            "incidents_by_source": dict(by_source),
        }

    # -------------------------------------------------------------------------
    # RESOURCES
    # -------------------------------------------------------------------------

    @staticmethod
    async def create_resource(db: AsyncIOMotorDatabase, resource_data: Union[ResourceModel, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(resource_data, ResourceModel):
            doc = resource_data.model_dump()
        else:
            doc = dict(resource_data)

        if "resource_id" not in doc or not doc["resource_id"]:
            random_suffix = uuid.uuid4().hex[:4].upper()
            doc["resource_id"] = f"RES-{random_suffix}"

        if "updated_at" not in doc or not doc["updated_at"]:
            doc["updated_at"] = datetime.now(timezone.utc)

        res = await db.resources.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    @staticmethod
    async def update_resource(
        db: AsyncIOMotorDatabase,
        resource_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        query = {"resource_id": resource_id}
        if ObjectId.is_valid(resource_id):
            query = {"$or": [{"resource_id": resource_id}, {"_id": ObjectId(resource_id)}]}

        update_fields = {k: v for k, v in update_data.items() if k not in ["_id", "resource_id"]}
        update_fields["updated_at"] = datetime.now(timezone.utc)

        res = await db.resources.update_one(query, {"$set": update_fields})
        if res.matched_count == 0:
            return None

        updated = await db.resources.find_one(query)
        return clean_mongo_doc(updated)

    @staticmethod
    async def find_nearby_resources(
        db: AsyncIOMotorDatabase,
        longitude: float,
        latitude: float,
        category: Optional[str] = None,
        status: Optional[str] = "AVAILABLE",
        max_distance_meters: float = 25000.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "$maxDistance": max_distance_meters
                }
            }
        }
        if status:
            query["status"] = status
        if category:
            query["category"] = category

        cursor = db.resources.find(query).limit(limit)
        docs = await cursor.to_list(length=limit)

        results = []
        for doc in docs:
            c = clean_mongo_doc(doc)
            coords = c.get("location", {}).get("coordinates", [])
            if len(coords) == 2:
                c["distance_km"] = round(haversine_distance_km(latitude, longitude, coords[1], coords[0]), 2)
            results.append(c)
        return results

    # -------------------------------------------------------------------------
    # HOSPITALS
    # -------------------------------------------------------------------------

    @staticmethod
    async def get_hospitals(
        db: AsyncIOMotorDatabase,
        status: Optional[str] = None,
        near_longitude: Optional[float] = None,
        near_latitude: Optional[float] = None,
        max_distance_meters: float = 30000.0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status

        if near_longitude is not None and near_latitude is not None:
            query["location"] = {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [near_longitude, near_latitude]
                    },
                    "$maxDistance": max_distance_meters
                }
            }

        cursor = db.hospitals.find(query).limit(limit)
        docs = await cursor.to_list(length=limit)

        results = []
        for doc in docs:
            c = clean_mongo_doc(doc)
            c["beds_available"] = c.get("beds_available", c.get("emergency_beds_available", 0))
            c["icu_available"] = c.get("icu_available", c.get("icu_beds_available", 0))
            c["emergency_capacity"] = c.get("emergency_capacity", c.get("emergency_beds_total", 0))

            if near_longitude is not None and near_latitude is not None:
                coords = c.get("location", {}).get("coordinates", [])
                if len(coords) == 2:
                    c["distance_km"] = round(haversine_distance_km(near_latitude, near_longitude, coords[1], coords[0]), 2)
            results.append(c)
        return results

    # -------------------------------------------------------------------------
    # NOTIFICATIONS
    # -------------------------------------------------------------------------

    @staticmethod
    async def create_notification(
        db: AsyncIOMotorDatabase,
        notification_data: Union[NotificationModel, Dict[str, Any]]
    ) -> Dict[str, Any]:
        if isinstance(notification_data, NotificationModel):
            doc = notification_data.model_dump()
        else:
            doc = dict(notification_data)

        if "notification_id" not in doc or not doc["notification_id"]:
            random_suffix = uuid.uuid4().hex[:4].upper()
            doc["notification_id"] = f"NOTIF-{random_suffix}"

        if "created_at" not in doc or not doc["created_at"]:
            doc["created_at"] = datetime.now(timezone.utc)
        if "read" not in doc:
            doc["read"] = False

        res = await db.notifications.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc
