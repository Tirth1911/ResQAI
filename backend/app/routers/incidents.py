import logging
from datetime import datetime, timezone
from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

from app.config import settings
from app.db import (
    get_assignments_collection,
    get_db,
    get_incidents_collection,
    get_resources_collection,
    to_geojson,
)
from app.models import (
    AlertLevel,
    AlertType,
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
    AlertOut,
    AssignmentOut,
    AssignmentStatusUpdate,
    DispatchRequest,
    DispatchResponse,
    IncidentDetailOut,
    IncidentOut,
    IncidentStatusUpdate,
    NotificationOut,
    RecommendationItem,
    RecommendationsOut,
    ReportIn,
    ReportOut,
    ReportResponse,
    ResourceOut,
    doc_to_alert_out,
    doc_to_assignment_out,
    doc_to_incident_out,
    doc_to_notification_out,
    doc_to_report_out,
    doc_to_resource_out,
)
from app.services.alerts import create_alert, run_alert_checks
from app.services.dedup import find_duplicate
from app.services.geo import haversine_km
from app.services.ingest import normalize_report
from app.services.realtime import broadcast
from app.services.recommend import get_recommendations
from app.services.triage import triage

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

# Severity escalation hierarchy for duplicate report thresholds
SEVERITY_BUMP: dict[IncidentSeverity, IncidentSeverity] = {
    IncidentSeverity.LOW: IncidentSeverity.MEDIUM,
    IncidentSeverity.MEDIUM: IncidentSeverity.HIGH,
    IncidentSeverity.HIGH: IncidentSeverity.CRITICAL,
    IncidentSeverity.CRITICAL: IncidentSeverity.CRITICAL,
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
    2) Triage classification (LLM with rule-based fallback)
    3) Deduplication check against active nearby incidents
    4) If duplicate: atomic merge into existing incident ($push, $inc, severity bump if count=3,6)
    5) Otherwise: insert new incident document with embedded report
    6) Broadcast realtime event (incident_merged or incident_created)
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

    # 4. Triage classification (LLM with rule-based fallback)
    triage_result = await triage(
        text=normalized_text,
        source=report_in.source.value,
        extra=report_in.extra,
    )

    # 5. Deduplication Check
    db = get_db()
    dup_match = await find_duplicate(db, report_in, triage_result)

    if dup_match is not None:
        target_incident, dup_score = dup_match
        current_count = target_incident.get("report_count", len(target_incident.get("reports", [])))
        new_count = current_count + 1

        update_ops: dict[str, Any] = {
            "$push": {"reports": report_doc},
            "$inc": {"report_count": 1},
            "$set": {
                "updated_at": now,
            },
        }

        # Severity escalation when report_count crosses 3 and 6
        if new_count in (3, 6):
            current_sev = IncidentSeverity(target_incident["severity"])
            bumped_sev = SEVERITY_BUMP[current_sev]
            bumped_pri = SEVERITY_PRIORITY_MAP[bumped_sev]
            update_ops["$set"]["severity"] = bumped_sev
            update_ops["$set"]["priority"] = bumped_pri

            if bumped_sev == IncidentSeverity.CRITICAL:
                await create_alert(
                    db,
                    type=AlertType.CRITICAL_INCIDENT,
                    level=AlertLevel.CRITICAL,
                    incident_id=target_incident["_id"],
                    message=(
                        f"CRITICAL ESCALATION: Multiple caller reports ({new_count}) "
                        f"elevated '{target_incident.get('title')}' to CRITICAL severity."
                    ),
                    now=now,
                )

        updated_doc = await db["incidents"].find_one_and_update(
            {"_id": target_incident["_id"]},
            update_ops,
            return_document=True,
        )

        incident_out = doc_to_incident_out(updated_doc)
        await broadcast(
            "incident_merged",
            {
                "incident": incident_out.model_dump(mode="json"),
                "duplicate_score": dup_score,
            },
        )

        return ReportResponse(
            incident_id=str(target_incident["_id"]),
            merged=True,
            duplicate_score=dup_score,
            incident=incident_out,
        )

    # If not a duplicate, create a new incident
    incident_doc: dict[str, Any] = {
        "title": title,
        "description": normalized_text,
        "type": triage_result.type,
        "severity": triage_result.severity,
        "priority": triage_result.priority,
        "status": IncidentStatus.TRIAGED,
        "location": geo_location,
        "address": report_in.address,
        "source": report_in.source,
        "report_count": 1,
        "reports": [report_doc],
        "ai_confidence": triage_result.confidence,
        "ai_reasoning": triage_result.reasoning,
        "classified_by": triage_result.classified_by,
        "ai_assist": None,
        "created_at": now,
        "updated_at": now,
        "resolved_at": None,
    }

    incidents_col = get_incidents_collection()
    res = await incidents_col.insert_one(incident_doc)
    incident_doc["_id"] = res.inserted_id

    # If critical severity, trigger critical_incident alert immediately
    if triage_result.severity == IncidentSeverity.CRITICAL:
        await create_alert(
            db,
            type=AlertType.CRITICAL_INCIDENT,
            level=AlertLevel.CRITICAL,
            incident_id=res.inserted_id,
            message=f"CRITICAL INCIDENT ALERT: {title} reported. Immediate deployment required.",
            now=now,
        )

    # Broadcast real-time creation event
    incident_out = doc_to_incident_out(incident_doc)
    await broadcast("incident_created", incident_out.model_dump(mode="json"))

    return ReportResponse(
        incident_id=str(res.inserted_id),
        merged=False,
        duplicate_score=None,
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


@router.get("/incidents/{id}/reports", response_model=list[ReportOut])
async def list_incident_reports(id: str) -> list[ReportOut]:
    """
    List all reports merged into this incident.
    """
    inc_oid = parse_object_id(id)
    incidents_col = get_incidents_collection()
    doc = await incidents_col.find_one({"_id": inc_oid})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{id}' not found",
        )

    return [doc_to_report_out(r) for r in doc.get("reports", [])]


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


# ==============================================================================
# Recommendations & Dispatch Endpoints
# ==============================================================================

@router.get("/incidents/{id}/recommendations", response_model=RecommendationsOut)
async def get_incident_recommendations(id: str) -> RecommendationsOut:
    """
    Get ranked resource recommendations for an incident using MongoDB $geoNear.
    """
    inc_oid = parse_object_id(id)
    db = get_db()
    incident = await db["incidents"].find_one({"_id": inc_oid})
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{id}' not found",
        )
    recs = await get_recommendations(db, incident)

    # Trigger resource shortage alert if units are below required quota
    if recs.shortage:
        await create_alert(
            db,
            type=AlertType.RESOURCE_SHORTAGE,
            level=AlertLevel.WARNING,
            incident_id=inc_oid,
            message=recs.shortage_detail or f"Resource shortage detected for incident '{incident.get('title')}'.",
        )

    return recs


@router.post("/incidents/{id}/dispatch", response_model=DispatchResponse)
async def dispatch_resources(id: str, req: DispatchRequest) -> DispatchResponse:
    """
    Dispatch recommended or chosen resources to an incident atomically.
    Prevents double dispatch with atomic find_one_and_update.
    """
    inc_oid = parse_object_id(id)
    db = get_db()
    incident = await db["incidents"].find_one({"_id": inc_oid})
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{id}' not found",
        )

    coords = incident["location"]["coordinates"]
    inc_lat, inc_lng = float(coords[1]), float(coords[0])

    # Determine target resource IDs
    target_rids: list[str] = []
    if req.auto:
        recs = await get_recommendations(db, incident)
        target_rids = [u.resource.id for u in recs.units]
    elif req.resource_ids:
        target_rids = req.resource_ids

    now = datetime.now(timezone.utc)
    created_assignments: list[AssignmentOut] = []
    skipped_rids: list[str] = []

    for rid_str in target_rids:
        if not ObjectId.is_valid(rid_str):
            skipped_rids.append(rid_str)
            continue
        rid = ObjectId(rid_str)

        # ATOMIC claim: only claims if status is available
        claimed = await db["resources"].find_one_and_update(
            {"_id": rid, "status": ResourceStatus.AVAILABLE},
            {"$set": {"status": ResourceStatus.ASSIGNED, "updated_at": now}},
            return_document=True,
        )

        if claimed is None:
            # Another dispatcher took this unit or unavailable
            skipped_rids.append(rid_str)
            continue

        res_coords = claimed["location"]["coordinates"]
        dist_km = haversine_km(inc_lat, inc_lng, float(res_coords[1]), float(res_coords[0]))
        eta_min = round((dist_km / 40.0) * 60.0 + 2.0, 1)

        asg_doc: dict[str, Any] = {
            "_id": ObjectId(),
            "incident_id": inc_oid,
            "resource_id": rid,
            "status": AssignmentStatus.ASSIGNED,
            "score": 0.95,
            "distance_km": round(dist_km, 2),
            "eta_min": eta_min,
            "assigned_at": now,
            "updated_at": now,
            "completed_at": None,
        }

        await db["assignments"].insert_one(asg_doc)
        asg_out = doc_to_assignment_out(asg_doc, resource_doc=claimed)
        created_assignments.append(asg_out)

        # Realtime broadcasts
        await broadcast("resource_updated", doc_to_resource_out(claimed).model_dump(mode="json"))
        await broadcast("assignment_updated", asg_out.model_dump(mode="json"))

    # Update incident status to dispatched if any units were dispatched
    if created_assignments and incident["status"] in (IncidentStatus.NEW, IncidentStatus.TRIAGED):
        incident = await db["incidents"].find_one_and_update(
            {"_id": inc_oid},
            {"$set": {"status": IncidentStatus.DISPATCHED, "updated_at": now}},
            return_document=True,
        )
        await broadcast("incident_updated", doc_to_incident_out(incident).model_dump(mode="json"))

    return DispatchResponse(
        incident=doc_to_incident_out(incident),
        assignments=created_assignments,
        skipped=skipped_rids,
    )


@router.patch("/assignments/{id}/status", response_model=AssignmentOut)
async def update_assignment_status(id: str, update: AssignmentStatusUpdate) -> AssignmentOut:
    """
    Update assignment lifecycle status and sync resource & incident statuses.
    - assigned -> en_route -> on_scene -> completed
    - Resource status moves to en_route, on_scene, or available (when completed)
    - Incident moves to en_route or on_scene accordingly
    """
    asg_oid = parse_object_id(id)
    db = get_db()
    asg = await db["assignments"].find_one({"_id": asg_oid})
    if not asg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment '{id}' not found",
        )

    now = datetime.now(timezone.utc)
    target_status = update.status
    inc_oid = asg["incident_id"]
    res_oid = asg["resource_id"]

    set_fields: dict[str, Any] = {
        "status": target_status,
        "updated_at": now,
    }
    if target_status == AssignmentStatus.COMPLETED:
        set_fields["completed_at"] = now

    updated_asg = await db["assignments"].find_one_and_update(
        {"_id": asg_oid},
        {"$set": set_fields},
        return_document=True,
    )

    # Sync resource status
    if target_status == AssignmentStatus.EN_ROUTE:
        await db["resources"].update_one(
            {"_id": res_oid},
            {"$set": {"status": ResourceStatus.EN_ROUTE, "updated_at": now}},
        )
    elif target_status == AssignmentStatus.ON_SCENE:
        await db["resources"].update_one(
            {"_id": res_oid},
            {"$set": {"status": ResourceStatus.ON_SCENE, "updated_at": now}},
        )
    elif target_status in (AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED):
        await db["resources"].update_one(
            {"_id": res_oid},
            {"$set": {"status": ResourceStatus.AVAILABLE, "updated_at": now}},
        )

    # Sync incident status (does NOT auto-resolve on complete)
    inc_doc = await db["incidents"].find_one({"_id": inc_oid})
    if inc_doc and inc_doc["status"] != IncidentStatus.RESOLVED:
        if target_status == AssignmentStatus.ON_SCENE:
            inc_doc = await db["incidents"].find_one_and_update(
                {"_id": inc_oid},
                {"$set": {"status": IncidentStatus.ON_SCENE, "updated_at": now}},
                return_document=True,
            )
        elif target_status == AssignmentStatus.EN_ROUTE and inc_doc["status"] != IncidentStatus.ON_SCENE:
            inc_doc = await db["incidents"].find_one_and_update(
                {"_id": inc_oid},
                {"$set": {"status": IncidentStatus.EN_ROUTE, "updated_at": now}},
                return_document=True,
            )

    res_doc = await db["resources"].find_one({"_id": res_oid})
    asg_out = doc_to_assignment_out(updated_asg, resource_doc=res_doc)

    await broadcast("assignment_updated", asg_out.model_dump(mode="json"))
    if res_doc:
        await broadcast("resource_updated", doc_to_resource_out(res_doc).model_dump(mode="json"))
    if inc_doc:
        await broadcast("incident_updated", doc_to_incident_out(inc_doc).model_dump(mode="json"))

    return asg_out


# ==============================================================================
# Alerts & Notifications Endpoints
# ==============================================================================

@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(acknowledged: Optional[bool] = None) -> list[AlertOut]:
    """
    List emergency system alerts with optional acknowledged filter.
    Sorted by created_at descending.
    """
    db = get_db()
    query: dict[str, Any] = {}
    if acknowledged is not None:
        query["acknowledged"] = acknowledged

    cursor = db["alerts"].find(query).sort("created_at", -1).limit(100)
    return [doc_to_alert_out(doc) async for doc in cursor]


@router.post("/alerts/{id}/ack", response_model=AlertOut)
async def acknowledge_alert(id: str) -> AlertOut:
    """
    Acknowledge an active alert by ID.
    """
    alert_oid = parse_object_id(id)
    db = get_db()
    now = datetime.now(timezone.utc)

    doc = await db["alerts"].find_one_and_update(
        {"_id": alert_oid},
        {"$set": {"acknowledged": True, "acknowledged_at": now}},
        return_document=True,
    )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{id}' not found",
        )

    return doc_to_alert_out(doc)


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications() -> list[NotificationOut]:
    """
    List recent multi-channel notifications (latest 100).
    Sorted by created_at descending.
    """
    db = get_db()
    cursor = db["notifications"].find({}).sort("created_at", -1).limit(100)
    return [doc_to_notification_out(doc) async for doc in cursor]


@router.post("/dev/tick")
async def dev_tick() -> dict[str, Any]:
    """
    Development & Demonstration trigger: runs delayed and escalation checks immediately.
    Only permitted when DEMO_MODE=true.
    """
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev tick endpoint is only enabled when DEMO_MODE=true",
        )

    db = get_db()
    alerts = await run_alert_checks(db)
    return {
        "status": "ok",
        "alerts_created": len(alerts),
        "demo_time_scale": settings.DEMO_TIME_SCALE,
    }


