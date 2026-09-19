import logging
from datetime import datetime, timezone
from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

from app.db import (
    get_assignments_collection,
    get_incidents_collection,
    get_resources_collection,
    to_geojson,
)
from app.models import (
    AssignmentStatus,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ReportSource,
    ResourceKind,
    ResourceStatus,
    SEVERITY_PRIORITY_MAP,
)
from app.schemas import (
    IncidentDetailOut,
    IncidentOut,
    IncidentStatusUpdate,
    ReportIn,
    ReportResponse,
    ResourceOut,
    doc_to_assignment_out,
    doc_to_incident_out,
    doc_to_resource_out,
)
from app.services.ingest import normalize_report
from app.services.realtime import broadcast

logger = logging.getLogger("resqai.incidents")

router = APIRouter(prefix="/api", tags=["incidents"])

# Allowed sequential transitions
ALLOWED_SEQUENTIAL_TRANSITIONS: dict[IncidentStatus, IncidentStatus] = {
    IncidentStatus.NEW: IncidentStatus.TRIAGED,
    IncidentStatus.TRIAGED: IncidentStatus.DISPATCHED,
    IncidentStatus.DISPATCHED: IncidentStatus.EN_ROUTE,
    IncidentStatus.EN_ROUTE: IncidentStatus.ON_SCENE,
    IncidentStatus.ON_SCENE: IncidentStatus.RESOLVED,
}


def parse_object_id(id_str: str) -> ObjectId:
    """Validate string and return ObjectId, raising 404 on invalid formats."""
    if not ObjectId.is_valid(id_str):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource not found: '{id_str}' is not a valid identifier",
        )
    return ObjectId(id_str)


# ==============================================================================
# Ingestion Endpoint
# ==============================================================================

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(report_in: ReportIn) -> ReportResponse:
    """
    Ingest multi-source emergency report.
    Pipeline:
    1) Normalize via services/ingest.py
    2) Deduplication hook (Step 5: for now always creates a new incident)
    3) Triage hook (Step 4: for now type=other, severity=medium)
    4) Insert incident document with embedded report
    5) Broadcast incident_created event
    """
    now = datetime.now(timezone.utc)
    reported_at = report_in.reported_at or now

    # 1. Normalize
    title, normalized_text = normalize_report(report_in)

    # 2. GeoJSON location Point: [lng, lat]
    geo_location = to_geojson(report_in.lat, report_in.lng)

    # 3. Embedded report shape
    report_doc = {
        "source": report_in.source,
        "reporter": report_in.reporter,
        "raw_text": normalized_text,
        "location": geo_location,
        "reported_at": reported_at,
    }

    # Default triage for Step 3 (hooks for Step 4 & 5 will refine this)
    incident_type = IncidentType.OTHER
    incident_severity = IncidentSeverity.MEDIUM
    priority = SEVERITY_PRIORITY_MAP[incident_severity]

    incident_doc: dict[str, Any] = {
        "title": title,
        "description": normalized_text,
        "type": incident_type,
        "severity": incident_severity,
        "priority": priority,
        "status": IncidentStatus.NEW,
        "location": geo_location,
        "address": report_in.address,
        "source": report_in.source,
        "report_count": 1,
        "reports": [report_doc],
        "ai_confidence": None,
        "ai_reasoning": None,
        "classified_by": "rules",
        "ai_assist": None,
        "created_at": now,
        "updated_at": now,
        "resolved_at": None,
    }

    incidents_col = get_incidents_collection()
    res = await incidents_col.insert_one(incident_doc)
    incident_doc["_id"] = res.inserted_id

    # 5. Broadcast real-time event
    incident_out = doc_to_incident_out(incident_doc)
    await broadcast("incident_created", incident_out.model_dump(mode="json"))

    return ReportResponse(
        incident_id=str(res.inserted_id),
        merged=False,
        incident=incident_out,
    )


# ==============================================================================
# Incident Query Endpoints
# ==============================================================================

@router.get("/incidents", response_model=list[IncidentOut])
async def list_incidents(
    status: Optional[IncidentStatus] = None,
    severity: Optional[IncidentSeverity] = None,
    type: Optional[IncidentType] = None,
    active_only: bool = False,
    limit: int = Query(default=200, ge=1, le=500),
) -> list[IncidentOut]:
    """
    List incidents with filtering by status, severity, type, and active status.
    Sorted by priority ascending (1=critical), then created_at descending.
    """
    query: dict[str, Any] = {}

    if status:
        query["status"] = status
    elif active_only:
        query["status"] = {"$ne": IncidentStatus.RESOLVED}

    if severity:
        query["severity"] = severity
    if type:
        query["type"] = type

    incidents_col = get_incidents_collection()
    cursor = incidents_col.find(query).sort([("priority", 1), ("created_at", -1)]).limit(limit)

    return [doc_to_incident_out(doc) async for doc in cursor]


@router.get("/incidents/{id}", response_model=IncidentDetailOut)
async def get_incident(id: str) -> IncidentDetailOut:
    """
    Get detailed incident by ID, including embedded reports and joined assignments with resource info.
    """
    inc_oid = parse_object_id(id)
    incidents_col = get_incidents_collection()
    doc = await incidents_col.find_one({"_id": inc_oid})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{id}' not found",
        )

    # Fetch assignments for this incident
    assignments_col = get_assignments_collection()
    asg_cursor = assignments_col.find({"incident_id": inc_oid})
    asg_docs = [a async for a in asg_cursor]

    # Join resource summaries for assignments
    res_map: dict[ObjectId, dict[str, Any]] = {}
    if asg_docs:
        res_ids = list({a["resource_id"] for a in asg_docs})
        resources_col = get_resources_collection()
        res_cursor = resources_col.find({"_id": {"$in": res_ids}})
        async for r in res_cursor:
            res_map[r["_id"]] = r

    assignments_out = [
        doc_to_assignment_out(a, resource_doc=res_map.get(a["resource_id"]))
        for a in asg_docs
    ]

    base_incident = doc_to_incident_out(doc)
    return IncidentDetailOut(
        **base_incident.model_dump(),
        assignments=assignments_out,
    )


@router.patch("/incidents/{id}/status", response_model=IncidentOut)
async def update_incident_status(
    id: str,
    update: IncidentStatusUpdate,
) -> IncidentOut:
    """
    Update incident lifecycle status with transition validation.
    Rules:
    - new -> triaged -> dispatched -> en_route -> on_scene -> resolved
    - Resolve is allowed from any active state
    - Resolving sets resolved_at and frees all assigned resources
    """
    inc_oid = parse_object_id(id)
    incidents_col = get_incidents_collection()
    doc = await incidents_col.find_one({"_id": inc_oid})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{id}' not found",
        )

    current_status = IncidentStatus(doc["status"])
    target_status = update.status

    # Check validity of transition
    is_valid = False
    if current_status == target_status:
        is_valid = True
    elif current_status != IncidentStatus.RESOLVED and target_status == IncidentStatus.RESOLVED:
        # Resolve allowed from any active state
        is_valid = True
    elif ALLOWED_SEQUENTIAL_TRANSITIONS.get(current_status) == target_status:
        # Allowed sequential step
        is_valid = True

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status transition from '{current_status.value}' to '{target_status.value}'. "
                f"Allowed sequential step: '{ALLOWED_SEQUENTIAL_TRANSITIONS.get(current_status, 'none')}' "
                f"or 'resolved'."
            ),
        )

    now = datetime.now(timezone.utc)
    set_fields: dict[str, Any] = {
        "status": target_status,
        "updated_at": now,
    }

    if target_status == IncidentStatus.RESOLVED:
        set_fields["resolved_at"] = now

        # Free all assigned resources
        assignments_col = get_assignments_collection()
        resources_col = get_resources_collection()

        active_asgs = await assignments_col.find({
            "incident_id": inc_oid,
            "status": {"$ne": AssignmentStatus.COMPLETED},
        }).to_list(length=100)

        if active_asgs:
            res_ids = [a["resource_id"] for a in active_asgs]
            # Set resources back to available
            await resources_col.update_many(
                {"_id": {"$in": res_ids}},
                {"$set": {"status": ResourceStatus.AVAILABLE, "updated_at": now}},
            )

            # Mark assignments as completed
            await assignments_col.update_many(
                {
                    "incident_id": inc_oid,
                    "status": {"$ne": AssignmentStatus.COMPLETED},
                },
                {
                    "$set": {
                        "status": AssignmentStatus.COMPLETED,
                        "completed_at": now,
                        "updated_at": now,
                    }
                },
            )

    updated_doc = await incidents_col.find_one_and_update(
        {"_id": inc_oid},
        {"$set": set_fields},
        return_document=True,
    )

    incident_out = doc_to_incident_out(updated_doc)
    await broadcast("incident_updated", incident_out.model_dump(mode="json"))

    return incident_out


# ==============================================================================
# Resources Endpoint
# ==============================================================================

@router.get("/resources", response_model=list[ResourceOut])
async def list_resources(
    kind: Optional[ResourceKind] = None,
    status: Optional[ResourceStatus] = None,
) -> list[ResourceOut]:
    """
    List emergency response resources with filtering by kind and status.
    Exposes coordinates as lat and lng.
    """
    query: dict[str, Any] = {}
    if kind:
        query["kind"] = kind
    if status:
        query["status"] = status

    resources_col = get_resources_collection()
    cursor = resources_col.find(query).sort("name", 1)

    return [doc_to_resource_out(doc) async for doc in cursor]
