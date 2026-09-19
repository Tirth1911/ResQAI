import math
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.config import settings
from backend.app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentPaginatedResponse,
    IncidentStatsResponse,
    IncidentActionRequest,
)
from backend.app.models.incident import IncidentStatus
from backend.app.services.db_service import DBService
from backend.app.services.duplicate_detector import (
    DuplicateDetector,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    RelatedIncidentsResponse,
)
from backend.app.services.resource_matcher import (
    ResourceMatcher,
    AssignResourceRequest,
    AssignResourceResponse,
)
from backend.app.ai.incident_classifier import (
    analyze_incident,
    analyze_and_update_incident_in_db,
    AIAnalysisResult,
)
from backend.app.websocket.manager import ws_manager, WebSocketEventType

router = APIRouter()


# -----------------------------------------------------------------------------
# 1. CREATE INCIDENT (WITH AUTO DEDUPLICATION CHECK)
# -----------------------------------------------------------------------------
@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED, summary="Report / Create an Emergency Incident", include_in_schema=False)
@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report / Create an Emergency Incident",
    description="Ingest an incident report. Automatically checks for duplicates in spatial/temporal proximity and merges into active incident if matching."
)
async def create_incident(
    incident_in: IncidentCreate,
    auto_dedup: bool = Query(True, description="Automatically merge duplicate incidents meeting distance, time, and text thresholds"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        lat = incident_in.location.latitude
        lon = incident_in.location.longitude

        # 1. Check for Duplicate if auto_dedup is enabled
        if auto_dedup:
            dedup_res = await DuplicateDetector.check_duplicate(
                db=db,
                title=incident_in.title,
                description=incident_in.description,
                latitude=lat,
                longitude=lon,
                reported_at=incident_in.reported_at
            )
            if dedup_res.is_duplicate and dedup_res.matched_incident_id:
                # Merge into existing master incident
                merged = await DuplicateDetector.merge_duplicate_report(
                    db=db,
                    matched_incident_id=dedup_res.matched_incident_id,
                    new_report_data=incident_in.model_dump(),
                    similarity_score=dedup_res.text_similarity or 0.85
                )
                if merged:
                    return merged

        # 2. Otherwise create new incident
        doc_data = incident_in.model_dump()
        loc = doc_data.pop("location")
        doc_data["location"] = {
            "type": "Point",
            "coordinates": [loc["longitude"], loc["latitude"]]
        }
        if not doc_data.get("address") and loc.get("address"):
            doc_data["address"] = loc["address"]
        elif not doc_data.get("address"):
            doc_data["address"] = f"Lat: {loc['latitude']:.5f}, Lon: {loc['longitude']:.5f}"

        # If AI analysis is enabled and classification needed
        if settings.ENABLE_AI_ANALYSIS and (not doc_data.get("ai_analysis") or not doc_data.get("type")):
            text = f"{doc_data['title']}. {doc_data['description']}"
            ai_res = await analyze_incident(
                description=text,
                source=doc_data.get("source", "citizen"),
                location=doc_data.get("address")
            )
            doc_data["ai_analysis"] = ai_res
            if not doc_data.get("type"):
                doc_data["type"] = ai_res["incident_type"]
            if not doc_data.get("severity"):
                doc_data["severity"] = ai_res["severity"]
            if not doc_data.get("priority"):
                doc_data["priority"] = ai_res["priority"]
            if not doc_data.get("confidence"):
                doc_data["confidence"] = ai_res["confidence"]

        created = await DBService.create_incident(db, doc_data)

        # Real-time WebSocket broadcast
        await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_CREATED, created)

        # Check for incident escalation and generate in-app/SMS/Email notifications
        from backend.app.services.alert_service import AlertService
        await AlertService.evaluate_incident_alerts(db, created)

        if str(created.get("severity", "")).upper() == "CRITICAL" or str(created.get("priority", "")).upper() == "P1":
            await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_ESCALATED, created)

        return created
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create incident: {str(e)}")


# -----------------------------------------------------------------------------
# 2. CHECK DUPLICATE ENDPOINT
# -----------------------------------------------------------------------------
@router.post(
    "/check-duplicate",
    response_model=DuplicateCheckResponse,
    summary="Check if Report is a Duplicate Incident",
    description="Evaluate whether a new emergency report is a duplicate of an existing active incident based on geographic distance (<=1km), time difference (<=45min), and description text similarity (>=80%)."
)
async def check_duplicate_incident(
    payload: DuplicateCheckRequest,
    distance_threshold_km: float = Query(settings.DISTANCE_THRESHOLD_KM, description="Max spatial distance in km"),
    time_threshold_minutes: int = Query(settings.TIME_THRESHOLD_MINUTES, description="Max temporal window in minutes"),
    text_similarity_threshold: float = Query(settings.TEXT_SIMILARITY_THRESHOLD, description="Min text similarity score 0.0-1.0"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await DuplicateDetector.check_duplicate(
        db=db,
        title=payload.title,
        description=payload.description,
        latitude=payload.location.get("latitude", 0.0),
        longitude=payload.location.get("longitude", 0.0),
        reported_at=payload.reported_at,
        distance_threshold_km=distance_threshold_km,
        time_threshold_minutes=time_threshold_minutes,
        text_similarity_threshold=text_similarity_threshold
    )


# -----------------------------------------------------------------------------
# 3. ASSIGN RESOURCE TO INCIDENT
# -----------------------------------------------------------------------------
@router.post(
    "/{incident_id}/assign-resource",
    response_model=AssignResourceResponse,
    summary="Assign Resource to Incident",
    description="Dispatches a resource to an incident: changes resource status to BUSY, sets current_incident_id, appends to incident assigned_resources, logs timeline dispatch event, and broadcasts WebSocket alert."
)
async def assign_resource_to_incident(
    incident_id: str,
    payload: AssignResourceRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        return await ResourceMatcher.assign_resource_to_incident(
            db=db,
            incident_id=incident_id,
            resource_id=payload.resource_id,
            actor=payload.actor,
            notes=payload.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to assign resource: {str(e)}")


# -----------------------------------------------------------------------------
# 4. LIST INCIDENTS (WITH PAGINATION & EXTENSIVE FILTERS)
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=IncidentPaginatedResponse,
    summary="List Emergency Incidents (Paginated & Filtered)",
    include_in_schema=False
)
@router.get(
    "/",
    response_model=IncidentPaginatedResponse,
    summary="List Emergency Incidents (Paginated & Filtered)",
    description="Retrieve emergency incidents with filtering by type, severity, priority, status, source, date range, or keyword search."
)
async def list_incidents(
    incident_type: Optional[str] = Query(None, alias="type", description="Filter by incident type (fire, flood, road_accident, etc.)"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    priority: Optional[str] = Query(None, description="Filter by priority (P1, P2, P3, P4)"),
    status: Optional[str] = Query(None, description="Filter by status (REPORTED, VERIFIED, DISPATCHED, IN_PROGRESS, RESOLVED, CLOSED)"),
    source: Optional[str] = Query(None, description="Filter by source channel (citizen, call_center, iot, field_team, etc.)"),
    start_date: Optional[datetime] = Query(None, description="Filter reported on or after UTC ISO timestamp"),
    end_date: Optional[datetime] = Query(None, description="Filter reported on or before UTC ISO timestamp"),
    search: Optional[str] = Query(None, description="Search keyword matching title, description, or address"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    items, total = await DBService.list_incidents(
        db=db,
        status=status,
        severity=severity,
        priority=priority,
        incident_type=incident_type,
        source=source,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        limit=limit
    )
    total_pages = math.ceil(total / limit) if total > 0 else 1
    return IncidentPaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


# -----------------------------------------------------------------------------
# 5. ACTIVE INCIDENTS
# -----------------------------------------------------------------------------
@router.get(
    "/active",
    response_model=IncidentPaginatedResponse,
    summary="Get Active Emergency Incidents",
    description="Retrieve all unresolved active incidents (REPORTED, VERIFIED, DISPATCHED, IN_PROGRESS)."
)
async def get_active_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    items, total = await DBService.get_active_incidents(db, page=page, limit=limit)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    return IncidentPaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


# -----------------------------------------------------------------------------
# 6. CRITICAL INCIDENTS
# -----------------------------------------------------------------------------
@router.get(
    "/critical",
    response_model=IncidentPaginatedResponse,
    summary="Get Critical Emergency Incidents",
    description="Retrieve all high-urgency incidents with severity CRITICAL or priority P1."
)
async def get_critical_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    items, total = await DBService.get_critical_incidents(db, page=page, limit=limit)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    return IncidentPaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


# -----------------------------------------------------------------------------
# 7. NEARBY INCIDENTS (2dsphere GEOSPATIAL SEARCH)
# -----------------------------------------------------------------------------
@router.get(
    "/nearby",
    response_model=List[IncidentResponse],
    summary="Find Nearby Incidents (2dsphere Proximity)",
    description="Find incidents located within a given radius (meters) of coordinates [longitude, latitude]."
)
async def find_nearby_incidents(
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Target longitude in decimal degrees"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Target latitude in decimal degrees"),
    max_distance_meters: float = Query(10000.0, ge=100.0, le=100000.0, description="Search radius in meters"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    severity: Optional[str] = Query(None, description="Optional severity filter"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await DBService.find_nearby_incidents(
        db=db,
        longitude=longitude,
        latitude=latitude,
        max_distance_meters=max_distance_meters,
        status=status,
        severity=severity,
        limit=limit
    )


# -----------------------------------------------------------------------------
# 8. INCIDENT STATS & AGGREGATIONS
# -----------------------------------------------------------------------------
@router.get(
    "/stats",
    response_model=IncidentStatsResponse,
    summary="Incident Statistics & Aggregations",
    description="Get real-time metric aggregates and counts grouped by type, severity, priority, status, and source."
)
async def get_incident_stats(db: AsyncIOMotorDatabase = Depends(get_database)):
    stats = await DBService.get_incident_stats(db)
    return IncidentStatsResponse(**stats)


# -----------------------------------------------------------------------------
# 9. GET RELATED & MERGED DUPLICATE REPORTS
# -----------------------------------------------------------------------------
@router.get(
    "/{incident_id}/related",
    response_model=RelatedIncidentsResponse,
    summary="Get Related & Merged Duplicate Incident Reports",
    description="Retrieve all duplicate calls merged into this master incident, full chronological timeline, and nearby active incidents."
)
async def get_related_incident_reports(
    incident_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    related = await DuplicateDetector.get_related_incidents(db, incident_id)
    if not related:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found."
        )
    return related


# -----------------------------------------------------------------------------
# 10. GET INCIDENT BY ID
# -----------------------------------------------------------------------------
@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get Incident by ID",
    description="Retrieve full details for an incident by human-readable ID (e.g. INC-20260919-0001) or MongoDB ObjectId."
)
async def get_incident(
    incident_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    incident = await DBService.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found."
        )
    return incident


# -----------------------------------------------------------------------------
# 11. PATCH INCIDENT (UPDATE)
# -----------------------------------------------------------------------------
@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Update Emergency Incident",
    description="Modify incident attributes, assign resources, or adjust severity/status."
)
async def update_incident(
    incident_id: str,
    incident_in: IncidentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    update_data = {k: v for k, v in incident_in.model_dump(exclude_unset=True).items() if v is not None}
    
    if "location" in update_data and update_data["location"]:
        loc = update_data.pop("location")
        update_data["location"] = {
            "type": "Point",
            "coordinates": [loc["longitude"], loc["latitude"]]
        }
        if loc.get("address"):
            update_data["address"] = loc["address"]

    for k in ["source", "type", "severity", "priority", "status"]:
        if k in update_data and hasattr(update_data[k], "value"):
            update_data[k] = update_data[k].value

    updated = await DBService.update_incident(db, incident_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found or update failed."
        )

    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, updated)
    if str(updated.get("severity", "")).upper() == "CRITICAL" or str(updated.get("priority", "")).upper() == "P1":
        await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_ESCALATED, updated)

    return updated


# -----------------------------------------------------------------------------
# 12. DELETE INCIDENT
# -----------------------------------------------------------------------------
@router.delete(
    "/{incident_id}",
    summary="Delete Incident",
    description="Remove an emergency incident record from MongoDB."
)
async def delete_incident(
    incident_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    success = await DBService.delete_incident(db, incident_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found."
        )

    await ws_manager.broadcast_event("INCIDENT_DELETED", {"incident_id": incident_id})
    return {"status": "deleted", "incident_id": incident_id}


# -----------------------------------------------------------------------------
# 13. AI INCIDENT INTELLIGENCE: ANALYZE INCIDENT
# -----------------------------------------------------------------------------
@router.post(
    "/{incident_id}/analyze",
    response_model=IncidentResponse,
    summary="Execute AI Incident Intelligence Analysis",
    description="Analyze the incident description using LLM / AI Intelligence Engine, update MongoDB fields (type, severity, priority, confidence, ai_analysis), and log to timeline."
)
async def trigger_ai_analysis(
    incident_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    updated = await analyze_and_update_incident_in_db(db, incident_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found."
        )
    return updated


# -----------------------------------------------------------------------------
# 14. ACTION: VERIFY INCIDENT
# -----------------------------------------------------------------------------
@router.post(
    "/{incident_id}/verify",
    response_model=IncidentResponse,
    summary="Verify Emergency Incident",
    description="Transition incident status to 'VERIFIED' and log verification action in timeline."
)
async def verify_incident(
    incident_id: str,
    action_in: Optional[IncidentActionRequest] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    actor = action_in.actor if action_in else "Command Dispatcher"
    notes = action_in.notes if action_in else "Incident verified through field reports / surveillance"
    
    updated = await DBService.transition_incident_status(
        db=db,
        incident_id=incident_id,
        new_status=IncidentStatus.VERIFIED.value,
        action_name="Incident Verified",
        actor=actor,
        notes=notes
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found."
        )

    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, updated)
    return updated


# -----------------------------------------------------------------------------
# 15. ACTION: RESOLVE INCIDENT
# -----------------------------------------------------------------------------
@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
    summary="Resolve Emergency Incident",
    description="Transition incident status to 'RESOLVED', signifying hazard containment."
)
async def resolve_incident(
    incident_id: str,
    action_in: Optional[IncidentActionRequest] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    actor = action_in.actor if action_in else "Command Dispatcher"
    notes = action_in.notes if action_in else "Incident contained and hazards mitigated"

    updated = await DBService.transition_incident_status(
        db=db,
        incident_id=incident_id,
        new_status=IncidentStatus.RESOLVED.value,
        action_name="Incident Resolved",
        actor=actor,
        notes=notes
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found."
        )

    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, updated)
    return updated


# -----------------------------------------------------------------------------
# 16. ACTION: CLOSE INCIDENT
# -----------------------------------------------------------------------------
@router.post(
    "/{incident_id}/close",
    response_model=IncidentResponse,
    summary="Close Emergency Incident",
    description="Transition incident status to 'CLOSED' for final case archival."
)
async def close_incident(
    incident_id: str,
    action_in: Optional[IncidentActionRequest] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    actor = action_in.actor if action_in else "Command Officer"
    notes = action_in.notes if action_in else "Case review completed and officially closed"

    updated = await DBService.transition_incident_status(
        db=db,
        incident_id=incident_id,
        new_status=IncidentStatus.CLOSED.value,
        action_name="Incident Closed",
        actor=actor,
        notes=notes
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found."
        )

    await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, updated)
    return updated
