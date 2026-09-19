from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
)
from backend.app.services.db_service import DBService, clean_mongo_docs, clean_mongo_doc
from backend.app.services.resource_matcher import (
    ResourceMatcher,
    IncidentRecommendationsResponse,
    ReleaseResourceResponse,
)
from backend.app.websocket.manager import ws_manager

router = APIRouter()


# -----------------------------------------------------------------------------
# 1. CREATE RESOURCE
# -----------------------------------------------------------------------------
@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED, summary="Create Emergency Resource")
async def create_resource(
    resource_in: ResourceCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    doc_data = resource_in.model_dump()
    loc = doc_data.pop("location")
    doc_data["location"] = {
        "type": "Point",
        "coordinates": [loc["longitude"], loc["latitude"]]
    }
    doc_data["category"] = doc_data["category"].value if hasattr(doc_data["category"], "value") else doc_data["category"]
    doc_data["status"] = doc_data["status"].value if hasattr(doc_data["status"], "value") else doc_data["status"]

    created = await DBService.create_resource(db, doc_data)

    await ws_manager.broadcast({
        "event": "RESOURCE_CREATED",
        "data": created
    })
    return created


# -----------------------------------------------------------------------------
# 2. RECOMMEND RESOURCES FOR INCIDENT
# -----------------------------------------------------------------------------
@router.get(
    "/recommend/{incident_id}",
    response_model=IncidentRecommendationsResponse,
    summary="Recommend Top Resources for Incident",
    description="Calculates top 5 ranked emergency resources based on: (distance_score * 0.50) + (capability_match * 0.30) + (readiness * 0.20)"
)
async def recommend_resources(
    incident_id: str,
    top_k: int = Query(5, ge=1, le=20, description="Number of top resources to recommend"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        return await ResourceMatcher.recommend_resources_for_incident(
            db=db,
            incident_id=incident_id,
            top_k=top_k
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate recommendations: {str(e)}")


# -----------------------------------------------------------------------------
# 3. RELEASE RESOURCE
# -----------------------------------------------------------------------------
@router.post(
    "/{resource_id}/release",
    response_model=ReleaseResourceResponse,
    summary="Release Emergency Resource (Mark AVAILABLE)",
    description="Releases a responder unit back to the available pool, clears current_incident_id, and broadcasts live WebSocket event."
)
async def release_resource(
    resource_id: str,
    actor: str = Query("Field Commander", description="Name/role of the releasing officer"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        return await ResourceMatcher.release_resource(
            db=db,
            resource_id=resource_id,
            actor=actor
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to release resource: {str(e)}")


# -----------------------------------------------------------------------------
# 4. LIST RESOURCES
# -----------------------------------------------------------------------------
@router.get("", response_model=List[ResourceResponse], summary="List Emergency Resources", include_in_schema=False)
@router.get("/", response_model=List[ResourceResponse], summary="List Emergency Resources")
async def list_resources(
    status: Optional[str] = Query(None, description="Filter by status (AVAILABLE, BUSY, EN_ROUTE, OFFLINE)"),
    category: Optional[str] = Query(None, description="Filter by category (AMBULANCE, FIRE_TRUCK, POLICE, etc.)"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    query = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category

    cursor = db.resources.find(query).limit(limit)
    docs = await cursor.to_list(length=limit)
    return clean_mongo_docs(docs)


# -----------------------------------------------------------------------------
# 5. NEARBY RESOURCES (2dsphere)
# -----------------------------------------------------------------------------
@router.get("/nearby", response_model=List[ResourceResponse], summary="Find Nearby Resources (2dsphere)")
async def find_nearby_resources(
    longitude: float = Query(..., ge=-180.0, le=180.0),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query("AVAILABLE"),
    max_distance_meters: float = Query(25000.0, ge=100.0, le=100000.0),
    limit: int = Query(10, ge=1, le=30),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await DBService.find_nearby_resources(
        db=db,
        longitude=longitude,
        latitude=latitude,
        category=category,
        status=status,
        max_distance_meters=max_distance_meters,
        limit=limit
    )


# -----------------------------------------------------------------------------
# 6. PATCH RESOURCE
# -----------------------------------------------------------------------------
@router.patch("/{resource_id}", response_model=ResourceResponse, summary="Update Resource Status / Location")
async def update_resource(
    resource_id: str,
    resource_in: ResourceUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    update_data = {k: v for k, v in resource_in.model_dump(exclude_unset=True).items() if v is not None}
    
    if "location" in update_data and update_data["location"]:
        loc = update_data.pop("location")
        update_data["location"] = {
            "type": "Point",
            "coordinates": [loc["longitude"], loc["latitude"]]
        }
    if "category" in update_data and hasattr(update_data["category"], "value"):
        update_data["category"] = update_data["category"].value
    if "status" in update_data and hasattr(update_data["status"], "value"):
        update_data["status"] = update_data["status"].value

    updated = await DBService.update_resource(db, resource_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Resource '{resource_id}' not found")

    await ws_manager.broadcast({
        "event": "RESOURCE_UPDATED",
        "data": updated
    })
    return updated
