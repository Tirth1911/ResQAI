from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.schemas.hospital import HospitalResponse, HospitalCreate
from backend.app.services.db_service import DBService, clean_mongo_doc

router = APIRouter()


@router.get("", response_model=List[HospitalResponse], summary="Get Emergency Hospitals (with Proximity)")
@router.get("/", response_model=List[HospitalResponse], include_in_schema=False)
async def get_hospitals(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, LIMITED, CLOSED)"),
    near_longitude: Optional[float] = Query(None, ge=-180.0, le=180.0),
    near_latitude: Optional[float] = Query(None, ge=-90.0, le=90.0),
    max_distance_meters: float = Query(30000.0, ge=500.0, le=200000.0),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Retrieve emergency hospitals, optionally ranked by 2dsphere proximity."""
    return await DBService.get_hospitals(
        db=db,
        status=status,
        near_longitude=near_longitude,
        near_latitude=near_latitude,
        max_distance_meters=max_distance_meters,
        limit=limit
    )


@router.post("/", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED, summary="Register Emergency Hospital")
async def create_hospital(
    hospital_in: HospitalCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    doc = hospital_in.model_dump()
    loc = doc.pop("location")
    doc["location"] = {
        "type": "Point",
        "coordinates": [loc["longitude"], loc["latitude"]]
    }
    doc["status"] = doc["status"].value if hasattr(doc["status"], "value") else doc["status"]
    
    res = await db.hospitals.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc
