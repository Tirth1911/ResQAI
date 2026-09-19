from datetime import datetime, timezone
from typing import Any, Optional
from bson import ObjectId
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection

from app.config import settings

import asyncio

# Global async Mongo client instance and its associated event loop
_client: Optional[AsyncMongoClient] = None
_client_loop: Optional[asyncio.AbstractEventLoop] = None


def get_client() -> AsyncMongoClient:
    """Return the global AsyncMongoClient instance, binding to the current event loop."""
    global _client, _client_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    needs_new = False
    if _client is None:
        needs_new = True
    elif current_loop is not None:
        client_internal_loop = getattr(_client, "_loop", None)
        if client_internal_loop is not None and client_internal_loop != current_loop:
            needs_new = True
        elif _client_loop is not None and _client_loop != current_loop:
            needs_new = True

    if needs_new:
        _client = AsyncMongoClient(
            settings.MONGODB_URI,
            tz_aware=True,
            serverSelectionTimeoutMS=5000,
        )
        _client_loop = current_loop

    return _client


async def close_client() -> None:
    """Close the global AsyncMongoClient connection."""
    global _client, _client_loop
    if _client is not None:
        try:
            await _client.close()
        except Exception:
            pass
        _client = None
        _client_loop = None


def get_db(db_name: Optional[str] = None) -> AsyncDatabase:
    """Return the active MongoDB database."""
    client = get_client()
    target_db = db_name or settings.MONGODB_DB
    return client[target_db]


def get_incidents_collection(db_name: Optional[str] = None) -> AsyncCollection:
    """Return the incidents collection."""
    return get_db(db_name)["incidents"]


def get_resources_collection(db_name: Optional[str] = None) -> AsyncCollection:
    """Return the resources collection."""
    return get_db(db_name)["resources"]


def get_assignments_collection(db_name: Optional[str] = None) -> AsyncCollection:
    """Return the assignments collection."""
    return get_db(db_name)["assignments"]


def get_alerts_collection(db_name: Optional[str] = None) -> AsyncCollection:
    """Return the alerts collection."""
    return get_db(db_name)["alerts"]


def get_notifications_collection(db_name: Optional[str] = None) -> AsyncCollection:
    """Return the notifications collection."""
    return get_db(db_name)["notifications"]


def to_geojson(lat: float, lng: float) -> dict[str, Any]:
    """Convert lat/lng to GeoJSON Point format: [lng, lat]."""
    return {
        "type": "Point",
        "coordinates": [float(lng), float(lat)],
    }


def from_geojson(doc_or_loc: dict[str, Any]) -> dict[str, float]:
    """
    Extract lat/lng from a GeoJSON dict or a document containing a location field.
    Returns a dict: {'lat': float, 'lng': float}.
    """
    if "coordinates" in doc_or_loc and isinstance(doc_or_loc["coordinates"], (list, tuple)):
        coords = doc_or_loc["coordinates"]
        return {"lat": float(coords[1]), "lng": float(coords[0])}

    if "location" in doc_or_loc and isinstance(doc_or_loc["location"], dict):
        coords = doc_or_loc["location"].get("coordinates", [])
        if len(coords) >= 2:
            return {"lat": float(coords[1]), "lng": float(coords[0])}

    raise ValueError(f"Cannot extract lat/lng from: {doc_or_loc}")


def serialize_doc(doc: Any) -> Any:
    """
    Recursively serialize MongoDB document for API responses:
    - Replaces '_id' with 'id' as string
    - Converts any ObjectId to string
    - Ensures datetimes are serialized to UTC ISO-8601 strings
    - Unpacks 'location' GeoJSON into top-level 'lat' and 'lng' if present
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result: dict[str, Any] = {}
        for key, val in doc.items():
            out_key = "id" if key == "_id" else key
            result[out_key] = serialize_doc(val)

        # Convenience conversion: if doc contains GeoJSON location Point and lacks top-level lat/lng
        if "location" in doc and isinstance(doc["location"], dict):
            coords = doc["location"].get("coordinates")
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                if "lng" not in result:
                    result["lng"] = float(coords[0])
                if "lat" not in result:
                    result["lat"] = float(coords[1])
        return result
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        if doc.tzinfo is None:
            return doc.replace(tzinfo=timezone.utc).isoformat()
        return doc.astimezone(timezone.utc).isoformat()
    return doc


async def ensure_indexes(db_name: Optional[str] = None) -> None:
    """
    Ensure all required indexes are created in MongoDB idempotently.
    - incidents: 2dsphere on location; (status, priority); created_at desc; (type, created_at desc)
    - resources: 2dsphere on location; (kind, status)
    - assignments: incident_id; resource_id; status
    - alerts: (incident_id, type, created_at desc); acknowledged
    - notifications: created_at desc
    """
    db = get_db(db_name)

    # incidents collection indexes
    incidents = db["incidents"]
    await incidents.create_index([("location", "2dsphere")])
    await incidents.create_index([("status", 1), ("priority", 1)])
    await incidents.create_index([("created_at", -1)])
    await incidents.create_index([("type", 1), ("created_at", -1)])

    # resources collection indexes
    resources = db["resources"]
    await resources.create_index([("location", "2dsphere")])
    await resources.create_index([("kind", 1), ("status", 1)])

    # assignments collection indexes
    assignments = db["assignments"]
    await assignments.create_index([("incident_id", 1)])
    await assignments.create_index([("resource_id", 1)])
    await assignments.create_index([("status", 1)])

    # alerts collection indexes
    alerts = db["alerts"]
    await alerts.create_index([("incident_id", 1), ("type", 1), ("created_at", -1)])
    await alerts.create_index([("acknowledged", 1)])

    # notifications collection indexes
    notifications = db["notifications"]
    await notifications.create_index([("created_at", -1)])

