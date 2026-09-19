import math
import pytest
from pymongo.asynchronous.database import AsyncDatabase

from app.models import ResourceKind
from app.schemas import doc_to_assignment_out, doc_to_incident_out, doc_to_resource_out
from app.seed import seed


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@pytest.mark.asyncio
async def test_seed_and_idempotency(test_db: AsyncDatabase):
    db_name = test_db.name

    # Reset and seed test database
    await seed(db_name=db_name, reset=True)

    # Verify counts
    res_count = await test_db["resources"].count_documents({})
    inc_count = await test_db["incidents"].count_documents({})
    asg_count = await test_db["assignments"].count_documents({})

    assert res_count == 35
    assert inc_count == 25
    assert asg_count == 25

    # Verify resource kind distribution
    assert await test_db["resources"].count_documents({"kind": ResourceKind.FIRE_TRUCK}) == 8
    assert await test_db["resources"].count_documents({"kind": ResourceKind.AMBULANCE}) == 8
    assert await test_db["resources"].count_documents({"kind": ResourceKind.POLICE_UNIT}) == 5
    assert await test_db["resources"].count_documents({"kind": ResourceKind.RESCUE_TEAM}) == 4
    assert await test_db["resources"].count_documents({"kind": ResourceKind.DISASTER_RESPONSE_TEAM}) == 2
    assert await test_db["resources"].count_documents({"kind": ResourceKind.HOSPITAL}) == 4
    assert await test_db["resources"].count_documents({"kind": ResourceKind.RELIEF_CAMP}) == 2
    assert await test_db["resources"].count_documents({"kind": ResourceKind.CONTROL_CENTER}) == 2

    # Verify idempotency: calling seed again without reset does not change counts
    await seed(db_name=db_name, reset=False)
    assert await test_db["resources"].count_documents({}) == 35
    assert await test_db["incidents"].count_documents({}) == 25


@pytest.mark.asyncio
async def test_indexes_exist(test_db: AsyncDatabase):
    res_indexes = await test_db["resources"].index_information()
    inc_indexes = await test_db["incidents"].index_information()
    asg_indexes = await test_db["assignments"].index_information()

    # Check 2dsphere on location
    assert any("2dsphere" in str(idx.get("key")) for idx in res_indexes.values())
    assert any("2dsphere" in str(idx.get("key")) for idx in inc_indexes.values())

    # Check assignment indexes
    assert any("incident_id" in str(idx.get("key")) for idx in asg_indexes.values())
    assert any("resource_id" in str(idx.get("key")) for idx in asg_indexes.values())


@pytest.mark.asyncio
async def test_near_query_sorted_by_distance(test_db: AsyncDatabase):
    ahmedabad_lng, ahmedabad_lat = 72.5714, 23.0225

    cursor = test_db["resources"].find({
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [ahmedabad_lng, ahmedabad_lat],
                }
            }
        }
    })

    results = [doc async for doc in cursor]
    assert len(results) == 35

    # Verify results are sorted by ascending distance
    distances = []
    for r in results:
        coords = r["location"]["coordinates"]
        dist = _haversine_km(ahmedabad_lat, ahmedabad_lng, coords[1], coords[0])
        distances.append(dist)

    # Allow tiny floating precision tolerance
    for i in range(len(distances) - 1):
        assert distances[i] <= distances[i + 1] + 0.05, f"Not sorted: {distances[i]} > {distances[i+1]}"


@pytest.mark.asyncio
async def test_schema_mappers(test_db: AsyncDatabase):
    sample_res = await test_db["resources"].find_one()
    assert sample_res is not None
    res_out = doc_to_resource_out(sample_res)
    assert isinstance(res_out.id, str)
    assert res_out.lat > 20.0
    assert res_out.lng > 70.0

    sample_inc = await test_db["incidents"].find_one()
    assert sample_inc is not None
    inc_out = doc_to_incident_out(sample_inc)
    assert isinstance(inc_out.id, str)
    assert len(inc_out.reports) > 0
    assert inc_out.reports[0].lat == inc_out.lat

    sample_asg = await test_db["assignments"].find_one()
    assert sample_asg is not None
    asg_out = doc_to_assignment_out(sample_asg, resource_doc=sample_res)
    assert isinstance(asg_out.id, str)
    assert asg_out.resource is not None
    assert asg_out.resource.id == str(sample_res["_id"])
