from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.db import db
from backend.app.services.ingest import normalize_report_text
from backend.app.services.triage import triage, map_severity_to_priority
from backend.app.services.dedup import find_duplicate
from backend.app.services.recommend import recommend_resources_for_incident
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


class DispatchIn(BaseModel):
    resource_ids: Optional[List[str]] = Field(default_factory=list)
    auto: bool = False


def validate_and_parse_id(id_str: str) -> Dict[str, Any]:
    """Helper to validate ObjectId or incident_id string and construct query filter without throwing 500."""
    if ObjectId.is_valid(id_str):
        return {"$or": [{"_id": ObjectId(id_str)}, {"incident_id": id_str}]}
    return {"incident_id": id_str}


def format_incident_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Format MongoDB document for API output."""
    if not doc:
        return {}
    res = dict(doc)
    if "_id" in res:
        res["id"] = str(res["_id"])
        res["_id"] = str(res["_id"])
    return res


def bump_severity_level(current_severity: str) -> Tuple[str, str]:
    """Bump severity level by 1 step (cap at critical) and return (new_severity, new_priority)."""
    sev = str(current_severity).lower()
    if sev in ["low"]:
        new_sev = "medium"
    elif sev in ["medium"]:
        new_sev = "high"
    elif sev in ["high", "critical"]:
        new_sev = "critical"
    else:
        new_sev = "medium"
    return new_sev, map_severity_to_priority(new_sev)


# -----------------------------------------------------------------------------
# 1. POST /api/reports - Ingest Multi-Source Emergency Report & AI Triage / Dedup
# -----------------------------------------------------------------------------
@router.post(
    "/reports",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Emergency Report with AI Triage & Deduplication",
    description="Ingest emergency report, normalize text, perform AI triage, deduplicate against active incidents, and create or merge."
)
async def create_report(report_in: ReportIn):
    norm_text = normalize_report_text(
        source=report_in.source.value,
        text=report_in.text,
        lat=report_in.lat,
        lng=report_in.lng,
        address=report_in.address,
        extra=report_in.extra
    )

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

    triage_res = await triage(
        text=norm_text,
        source=report_in.source.value,
        extra=report_in.extra
    )

    dup_match = await find_duplicate(
        db=db.db,
        new_report=report_embedded,
        triage_result=triage_res
    )

    if dup_match:
        master_inc, dup_score = dup_match
        inc_id = master_inc["_id"]

        current_count = master_inc.get("report_count", len(master_inc.get("reports", [])))
        new_count = current_count + 1

        update_set: Dict[str, Any] = {
            "updated_at": now_dt,
            "report_count": new_count
        }

        if new_count in [3, 6]:
            curr_sev = master_inc.get("severity", triage_res.severity)
            new_sev, new_prio = bump_severity_level(curr_sev)
            update_set["severity"] = new_sev
            update_set["priority"] = new_prio

        update_doc = {
            "$push": {"reports": report_embedded},
            "$set": update_set
        }

        await db.incidents.update_one({"_id": inc_id}, update_doc)
        updated_master = await db.incidents.find_one({"_id": inc_id})

        return {
            "merged": True,
            "incident_id": str(inc_id),
            "duplicate_score": dup_score,
            "incident": format_incident_doc(updated_master)
        }

    inc_obj_id = ObjectId()
    inc_code = f"INC-{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    await db.reports.insert_one({"_id": ObjectId(), "incident_id": inc_code, **report_embedded})

    incident_doc = {
        "_id": inc_obj_id,
        "incident_id": inc_code,
        "source": report_in.source.value,
        "type": triage_res.type,
        "severity": triage_res.severity,
        "priority": triage_res.priority,
        "status": "triaged",
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
        "ai_confidence": triage_res.confidence,
        "ai_reasoning": triage_res.reasoning,
        "classified_by": triage_res.classified_by,
        "report_count": 1,
        "reports": [report_embedded],
        "assignments": []
    }

    await db.incidents.insert_one(incident_doc)
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
# 3. GET /api/incidents/{id}/recommendations - Get Resource Recommendations
# -----------------------------------------------------------------------------
@router.get(
    "/incidents/{id}/recommendations",
    summary="Get Resource Recommendations",
    description="Ranked recommendations ($geoNear) for units, nearest hospital, relief camp, and shortage detection."
)
async def get_incident_recommendations(id: str):
    filter_q = validate_and_parse_id(id)
    incident = await db.incidents.find_one(filter_q)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return await recommend_resources_for_incident(db.db, incident)


# -----------------------------------------------------------------------------
# 4. POST /api/incidents/{id}/dispatch - Dispatch Resources to Incident
# -----------------------------------------------------------------------------
@router.post(
    "/incidents/{id}/dispatch",
    summary="Dispatch Resources to Incident",
    description="Atomically claims available units, creates assignments, updates incident status to dispatched."
)
async def dispatch_incident_resources(id: str, body: DispatchIn):
    filter_q = validate_and_parse_id(id)
    incident = await db.incidents.find_one(filter_q)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    target_rids = body.resource_ids or []
    if body.auto or not target_rids:
        recs = await recommend_resources_for_incident(db.db, incident)
        recommended_units = recs.get("units", [])
        target_rids = [u["resource_id"] for u in recommended_units]

    dispatched = []
    unclaimed = []
    now_dt = datetime.now(timezone.utc)
    inc_code = incident.get("incident_id")
    inc_obj_id = incident.get("_id")

    for rid in target_rids:
        query_r = {
            "$or": [{"resource_id": rid}, {"_id": ObjectId(rid) if ObjectId.is_valid(rid) else rid}],
            "status": {"$in": ["available", "AVAILABLE"]}
        }
        update_r = {
            "$set": {
                "status": "assigned",
                "current_incident_id": str(inc_code or inc_obj_id),
                "updated_at": now_dt
            }
        }

        claimed = await db.resources.find_one_and_update(query_r, update_r, return_document=True)
        if not claimed:
            unclaimed.append(rid)
            continue

        r_code = claimed.get("resource_id", str(claimed["_id"]))
        asgn_doc = {
            "_id": ObjectId(),
            "assignment_id": f"ASG-{int(now_dt.timestamp() * 1000)}",
            "incident_id": str(inc_code or inc_obj_id),
            "resource_id": r_code,
            "resource_name": claimed.get("name") or claimed.get("resource_name") or r_code,
            "kind": claimed.get("kind") or claimed.get("category"),
            "status": "assigned",
            "assigned_at": now_dt,
            "completed": False,
            "completed_at": None
        }

        await db.assignments.insert_one(asgn_doc)
        dispatched.append(format_incident_doc(claimed))

    if dispatched:
        dispatched_codes = [d.get("resource_id", d.get("id")) for d in dispatched]
        await db.incidents.update_one(
            {"_id": incident["_id"]},
            {
                "$set": {
                    "status": "dispatched",
                    "updated_at": now_dt
                },
                "$addToSet": {
                    "assigned_resources": {"$each": dispatched_codes}
                }
            }
        )

    updated_inc = await db.incidents.find_one({"_id": incident["_id"]})
    return {
        "dispatched": dispatched,
        "unclaimed": unclaimed,
        "incident": format_incident_doc(updated_inc)
    }


# -----------------------------------------------------------------------------
# 5. GET /api/incidents/{id} - Get Detailed Incident by ID
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

    assignments = await db.assignments.find({
        "$or": [{"incident_id": inc_code}, {"incident_id": str(inc_obj_id)}]
    }).to_list(100)

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

    reports = await db.reports.find({
        "$or": [{"incident_id": inc_code}, {"incident_id": str(inc_obj_id)}]
    }).to_list(100)

    for r in reports:
        r["_id"] = str(r["_id"])

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
# 6. GET /api/incidents/{id}/reports - List Merged Reports for Incident
# -----------------------------------------------------------------------------
@router.get(
    "/incidents/{id}/reports",
    summary="Get Merged Reports for Incident",
    description="Retrieve all embedded/merged reports associated with an incident case."
)
async def get_incident_reports(id: str):
    filter_q = validate_and_parse_id(id)
    incident = await db.incidents.find_one(filter_q)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return incident.get("reports", [])


# -----------------------------------------------------------------------------
# 7. PATCH /api/incidents/{id}/status - Transition Incident Status
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

        await db.assignments.update_many(
            {"$or": [{"incident_id": inc_code}, {"incident_id": str(inc_obj_id)}]},
            {"$set": {"completed": True, "completed_at": now_dt}}
        )

    await db.incidents.update_one({"_id": incident["_id"]}, {"$set": update_fields})
    updated_doc = await db.incidents.find_one({"_id": incident["_id"]})
    return format_incident_doc(updated_doc)


# -----------------------------------------------------------------------------
# 8. PATCH /api/assignments/{id}/status - Sync Assignment, Resource & Incident Status
# -----------------------------------------------------------------------------
@router.patch(
    "/assignments/{id}/status",
    summary="Update Assignment Status",
    description="Syncs assignment (assigned->en_route->on_scene->completed), resource, and incident status."
)
async def update_assignment_status(id: str, body: StatusUpdateIn):
    query_a = validate_and_parse_id(id)
    if not ObjectId.is_valid(id):
        query_a = {"$or": [{"assignment_id": id}, {"_id": id}]}

    asgn = await db.assignments.find_one(query_a)
    if not asgn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    new_status = body.status.lower().strip()
    now_dt = datetime.now(timezone.utc)

    update_fields: Dict[str, Any] = {"status": new_status}
    if new_status == "completed":
        update_fields["completed"] = True
        update_fields["completed_at"] = now_dt

    await db.assignments.update_one({"_id": asgn["_id"]}, {"$set": update_fields})

    inc_id = asgn.get("incident_id")
    res_id = asgn.get("resource_id")

    # Sync Resource Status
    if res_id:
        r_query = {"$or": [{"resource_id": res_id}, {"_id": ObjectId(res_id) if ObjectId.is_valid(res_id) else res_id}]}
        if new_status == "completed":
            await db.resources.update_one(r_query, {"$set": {"status": "available", "current_incident_id": None, "updated_at": now_dt}})
        elif new_status in ["en_route", "on_scene"]:
            await db.resources.update_one(r_query, {"$set": {"status": new_status, "updated_at": now_dt}})

    # Sync Incident Status (en_route when any assignment is en_route, on_scene when any is on_scene)
    if inc_id and new_status in ["en_route", "on_scene"]:
        inc_query = validate_and_parse_id(inc_id)
        inc_doc = await db.incidents.find_one(inc_query)
        if inc_doc:
            current_inc_status = str(inc_doc.get("status", "")).lower()
            if new_status == "on_scene" or (new_status == "en_route" and current_inc_status != "on_scene"):
                await db.incidents.update_one({"_id": inc_doc["_id"]}, {"$set": {"status": new_status, "updated_at": now_dt}})

    updated_asgn = await db.assignments.find_one({"_id": asgn["_id"]})
    return format_incident_doc(updated_asgn)


# -----------------------------------------------------------------------------
# 9. GET /api/resources - List Resources with Location (lat/lng)
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
