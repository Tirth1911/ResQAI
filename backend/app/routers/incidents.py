from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict

from backend.app.db import db
from backend.app.services.ingest import normalize_report_text
from backend.app.services.realtime import broadcast_incident_created

router = APIRouter()


class ReportSource(str, Enum):
    CALL_911 = "call_911"
    IOT_SENSOR = "iot_sensor"
    HOSPITAL = "hospital"
    CITIZEN = "citizen"
    SOCIAL_MEDIA = "social_media"
    FIELD_UNIT = "field_unit"


class ReportIn(BaseModel):
    source: ReportSource
    reporter: Optional[str] = None
    text: str
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    address: Optional[str] = None
    reported_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    extra: Optional[Dict[str, Any]] = None


class StatusUpdateIn(BaseModel):
    status: str


def validate_and_parse_id(id_str: str) -> Dict[str, Any]:
    """Helper to validate ObjectId or incident_id string and construct query filter without throwing 500."""
    if ObjectId.is_valid(id_str):
        return {"$or": [{"_id": ObjectId(id_str)}, {"incident_id": id_str}]}
    return {"incident_id": id_str}


def format_incident_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Format MongoDB incident document for API output."""
    res = dict(doc)
    if "_id" in res:
        res["id"] = str(res["_id"])
        res["_id"] = str(res["_id"])
    return res


# -----------------------------------------------------------------------------
# 1. POST /api/reports - Ingest Multi-Source Emergency Report
# -----------------------------------------------------------------------------
@router.post(
    "/reports",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Emergency Report",
    description="Ingest multi-source emergency report (call_911, iot_sensor, hospital, citizen, social_media, field_unit)"
)
async def create_report(report_in: ReportIn):
    # Step 1: Normalize via services/ingest.py
    norm_text = normalize_report_text(
        source=report_in.source.value,
        text=report_in.text,
        lat=report_in.lat,
        lng=report_in.lng,
        address=report_in.address,
        extra=report_in.extra
    )

    # Step 2: Dedup hook (always create new incident for now)
    # Step 3: Triage hook (type=other, severity=medium, priority=P3, status=new)
    inc_obj_id = ObjectId()
    inc_code = f"INC-{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    reported_dt = report_in.reported_at or datetime.now(timezone.utc)
    if reported_dt.tzinfo is None:
        reported_dt = reported_dt.replace(tzinfo=timezone.utc)

    now_dt = datetime.now(timezone.utc)

    report_embedded = {
        "source": report_in.source.value,
        "reporter": report_in.reporter,
        "text": report_in.text,
        "normalized_text": norm_text,
        "lat": report_in.lat,
        "lng": report_in.lng,
        "address": report_in.address or f"Lat: {report_in.lat:.4f}, Lng: {report_in.lng:.4f}",
        "reported_at": reported_dt,
        "extra": report_in.extra or {}
    }

    # Store individual report document in reports collection
    await db.reports.insert_one({"_id": ObjectId(), "incident_id": inc_code, **report_embedded})

    incident_doc = {
        "_id": inc_obj_id,
        "incident_id": inc_code,
        "source": report_in.source.value,
        "type": "other",
        "severity": "medium",
        "priority": "P3",
        "status": "new",
        "title": norm_text[:80],
        "description": norm_text,
        "location": {
            "type": "Point",
            "coordinates": [report_in.lng, report_in.lat]
        },
        "address": report_in.address or f"Lat: {report_in.lat:.4f}, Lng: {report_in.lng:.4f}",
        "reported_at": reported_dt,
        "created_at": now_dt,
        "updated_at": now_dt,
        "resolved_at": None,
        "reports": [report_embedded],
        "assignments": []
    }

    # Step 4: Insert the incident document
    await db.incidents.insert_one(incident_doc)

    # Step 5: Broadcast incident_created
    await broadcast_incident_created(incident_doc)

    formatted_inc = format_incident_doc(incident_doc)
    return {
        "incident_id": str(inc_obj_id),
        "merged": False,
        "incident": formatted_inc
    }


# -----------------------------------------------------------------------------
# 2. GET /api/incidents - List Incidents (Filtered & Sorted)
# -----------------------------------------------------------------------------
@router.get(
    "/incidents",
    summary="Get List of Incidents",
    description="Filters status, severity, type, active_only; sorted by priority asc then created_at desc."
)
async def get_incidents(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    type_filter: Optional[str] = Query(None, alias="type"),
    active_only: bool = Query(False),
    limit: int = Query(200, ge=1, le=500)
):
    query: Dict[str, Any] = {}

    if status_filter:
        query["status"] = status_filter.lower()
    elif active_only:
        query["status"] = {"$nin": ["resolved", "closed", "RESOLVED", "CLOSED"]}

    if severity:
        query["severity"] = {"$regex": f"^{severity}$", "$options": "i"}

    if type_filter:
        query["type"] = type_filter.lower()

    cursor = db.incidents.find(query).sort([("priority", 1), ("created_at", -1)]).limit(limit)
    raw_docs = await cursor.to_list(length=limit)

    return [format_incident_doc(doc) for doc in raw_docs]


# -----------------------------------------------------------------------------
# 3. GET /api/incidents/{id} - Get Detailed Incident by ID
# -----------------------------------------------------------------------------
@router.get(
    "/incidents/{id}",
    summary="Get Incident Details by ID",
    description="Retrieve incident joined with reports and assignments. Returns 404 for invalid/missing ID."
)
async def get_incident_by_id(id: str):
    filter_q = validate_and_parse_id(id)
    incident = await db.incidents.find_one(filter_q)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    inc_code = incident.get("incident_id")
    inc_obj_id = incident.get("_id")

    # Join assignments
    assignments = await db.assignments.find({
        "$or": [{"incident_id": inc_code}, {"incident_id": str(inc_obj_id)}]
    }).to_list(100)

    # Join resource info if assignments exist
    if assignments:
        res_ids = [a.get("resource_id") for a in assignments if a.get("resource_id")]
        resources = await db.resources.find({"resource_id": {"$in": res_ids}}).to_list(100)
        res_map = {r.get("resource_id"): r for r in resources}

        for a in assignments:
            a["_id"] = str(a["_id"])
            rid = a.get("resource_id")
            if rid in res_map:
                r_info = res_map[rid]
                a["resource_name"] = r_info.get("name") or r_info.get("resource_name")
                a["kind"] = r_info.get("kind") or r_info.get("category")
                a["status"] = r_info.get("status")

    # Join reports if any standalone reports exist in db.reports
    reports = await db.reports.find({
        "$or": [{"incident_id": inc_code}, {"incident_id": str(inc_obj_id)}]
    }).to_list(100)

    for r in reports:
        r["_id"] = str(r["_id"])

    # Merge reports list
    embedded_reports = incident.get("reports", [])
    if reports:
        for r in reports:
            if r not in embedded_reports:
                embedded_reports.append(r)

    result = format_incident_doc(incident)
    result["reports"] = embedded_reports
    result["assignments"] = [format_incident_doc(a) for a in assignments]

    return result


# -----------------------------------------------------------------------------
# 4. PATCH /api/incidents/{id}/status - Transition Incident Status
# -----------------------------------------------------------------------------
ALLOWED_TRANSITIONS = {
    "new": ["triaged", "resolved"],
    "triaged": ["dispatched", "resolved"],
    "dispatched": ["en_route", "resolved"],
    "en_route": ["on_scene", "resolved"],
    "on_scene": ["resolved"],
    "resolved": [],
    "closed": []
}

ACTIVE_STATES = {"new", "triaged", "dispatched", "en_route", "on_scene"}


@router.patch(
    "/incidents/{id}/status",
    summary="Update Incident Status",
    description="Validates allowed transitions (new->triaged->dispatched->en_route->on_scene->resolved; resolve allowed from any active state)."
)
async def update_incident_status(id: str, body: StatusUpdateIn):
    filter_q = validate_and_parse_id(id)
    incident = await db.incidents.find_one(filter_q)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    current_status = str(incident.get("status", "new")).lower()
    target_status = body.status.lower().strip()

    # Validate transition
    valid_next = ALLOWED_TRANSITIONS.get(current_status, [])
    is_allowed = (target_status in valid_next) or (target_status == "resolved" and current_status in ACTIVE_STATES)

    if not is_allowed and target_status != current_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{current_status}' to '{target_status}'"
        )

    now_dt = datetime.now(timezone.utc)
    update_fields: Dict[str, Any] = {
        "status": target_status,
        "updated_at": now_dt
    }

    if target_status == "resolved":
        update_fields["resolved_at"] = now_dt
        inc_code = incident.get("incident_id")
        inc_obj_id = incident.get("_id")

        # Free assigned resources
        await db.resources.update_many(
            {"$or": [{"current_incident_id": inc_code}, {"current_incident_id": str(inc_obj_id)}]},
            {"$set": {"status": "available", "current_incident_id": None}}
        )

        assigned_list = incident.get("assigned_resources", [])
        if assigned_list:
            await db.resources.update_many(
                {"resource_id": {"$in": assigned_list}},
                {"$set": {"status": "available", "current_incident_id": None}}
            )

        # Complete assignments
        await db.assignments.update_many(
            {"$or": [{"incident_id": inc_code}, {"incident_id": str(inc_obj_id)}]},
            {"$set": {"completed": True, "completed_at": now_dt}}
        )

    await db.incidents.update_one({"_id": incident["_id"]}, {"$set": update_fields})
    updated_doc = await db.incidents.find_one({"_id": incident["_id"]})
    return format_incident_doc(updated_doc)


# -----------------------------------------------------------------------------
# 5. GET /api/resources - List Resources with Location (lat/lng)
# -----------------------------------------------------------------------------
@router.get(
    "/resources",
    summary="Get List of Resources",
    description="Filters kind, status; returns lat/lng coordinates for each resource."
)
async def get_resources(
    kind: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status")
):
    query: Dict[str, Any] = {}

    if kind:
        query["$or"] = [
            {"kind": {"$regex": f"^{kind}$", "$options": "i"}},
            {"category": {"$regex": f"^{kind}$", "$options": "i"}},
            {"type": {"$regex": f"^{kind}$", "$options": "i"}}
        ]

    if status_filter:
        query["status"] = {"$regex": f"^{status_filter}$", "$options": "i"}

    cursor = db.resources.find(query)
    resources = await cursor.to_list(500)

    results = []
    for r in resources:
        res_item = format_incident_doc(r)
        # Extract lat/lng
        lat = 0.0
        lng = 0.0
        if "location" in r and isinstance(r["location"], dict):
            coords = r["location"].get("coordinates", [0.0, 0.0])
            if len(coords) >= 2:
                lng, lat = coords[0], coords[1]
        elif "latitude" in r and "longitude" in r:
            lat = r["latitude"]
            lng = r["longitude"]
        elif "lat" in r and "lng" in r:
            lat = r["lat"]
            lng = r["lng"]

        res_item["lat"] = lat
        res_item["lng"] = lng
        results.append(res_item)

    return results
