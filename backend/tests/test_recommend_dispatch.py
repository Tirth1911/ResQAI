import asyncio
from datetime import datetime, timezone
from bson import ObjectId
import pytest
from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.models import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ResourceKind,
    ResourceStatus,
)
from app.seed import seed


@pytest.mark.asyncio
async def test_recommendations_and_distance_ordering(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify resource recommendation ordering, explainability, hospital and relief camp detection."""
    await seed(db_name=test_db.name, reset=True)

    # Create a critical fire incident near Navrangpura
    create_resp = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Massive spreading blaze and explosion in commercial tower, multiple casualties trapped.",
            "lat": 23.0365,
            "lng": 72.5610,
        },
    )
    assert create_resp.status_code == 201
    inc_id = create_resp.json()["incident_id"]

    # Request recommendations
    rec_resp = await async_client.get(f"/api/incidents/{inc_id}/recommendations")
    assert rec_resp.status_code == 200
    recs = rec_resp.json()

    assert len(recs["units"]) > 0
    # Explainability reason check
    first_unit = recs["units"][0]
    assert "km away" in first_unit["reason"]
    assert "ETA" in first_unit["reason"]
    assert first_unit["score"] > 0
    assert first_unit["distance_km"] >= 0

    # Hospital must be recommended
    assert recs["hospital"] is not None
    assert recs["hospital"]["kind"] == "hospital"
    assert recs["hospital"]["capacity"] > 0

    # Critical severity includes relief camp
    assert recs["relief_camp"] is not None
    assert recs["relief_camp"]["kind"] == "relief_camp"


@pytest.mark.asyncio
async def test_exclusion_of_busy_units(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify that units with status other than 'available' are excluded from recommendations."""
    await seed(db_name=test_db.name, reset=True)

    create_resp = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Fire burning in warehouse.",
            "lat": 23.0365,
            "lng": 72.5610,
        },
    )
    inc_id = create_resp.json()["incident_id"]

    rec_resp1 = await async_client.get(f"/api/incidents/{inc_id}/recommendations")
    units1 = rec_resp1.json()["units"]
    top_res_id = units1[0]["resource"]["id"]

    # Mark top unit as busy
    await test_db["resources"].update_one(
        {"_id": ObjectId(top_res_id)},
        {"$set": {"status": ResourceStatus.ASSIGNED}},
    )

    rec_resp2 = await async_client.get(f"/api/incidents/{inc_id}/recommendations")
    units2 = rec_resp2.json()["units"]
    assert all(u["resource"]["id"] != top_res_id for u in units2)


@pytest.mark.asyncio
async def test_shortage_detection(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify shortage=True when fewer units than required by severity are available."""
    await seed(db_name=test_db.name, reset=True)

    # Set almost all fire engines to offline so there is a shortage
    await test_db["resources"].update_many(
        {"kind": ResourceKind.FIRE_TRUCK},
        {"$set": {"status": ResourceStatus.OFFLINE}},
    )
    # Leave just one fire truck available
    avail = await test_db["resources"].find_one({"kind": ResourceKind.FIRE_TRUCK})
    await test_db["resources"].update_one(
        {"_id": avail["_id"]},
        {"$set": {"status": ResourceStatus.AVAILABLE}},
    )

    create_resp = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Massive chemical explosion with multiple casualties trapped inside factory blaze.",
            "lat": 23.0365,
            "lng": 72.5610,
        },
    )
    inc_id = create_resp.json()["incident_id"]

    rec_resp = await async_client.get(f"/api/incidents/{inc_id}/recommendations")
    assert rec_resp.status_code == 200
    data = rec_resp.json()

    # Critical incident requires 5 units
    if len(data["units"]) < 5:
        assert data["shortage"] is True
        assert data["shortage_detail"] is not None
        assert "Required 5 units" in data["shortage_detail"]


@pytest.mark.asyncio
async def test_dispatch_and_state_machine_sync(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """
    Verify complete dispatch state machine and synchronization:
    - Auto dispatch sets incident=dispatched and resources=assigned
    - Assignment en_route -> resource=en_route, incident=en_route
    - Assignment on_scene -> resource=on_scene, incident=on_scene
    - Assignment completed -> resource=available (freed), incident remains on_scene
    """
    await seed(db_name=test_db.name, reset=True)

    create_resp = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Car collision and overturned truck.",
            "lat": 23.0285,
            "lng": 72.5070,
        },
    )
    inc_id = create_resp.json()["incident_id"]

    # 1. Dispatch with auto: true
    dispatch_resp = await async_client.post(
        f"/api/incidents/{inc_id}/dispatch",
        json={"auto": True},
    )
    assert dispatch_resp.status_code == 200
    disp_data = dispatch_resp.json()
    assert disp_data["incident"]["status"] == "dispatched"
    assert len(disp_data["assignments"]) > 0

    first_asg = disp_data["assignments"][0]
    asg_id = first_asg["id"]
    res_id = first_asg["resource_id"]

    # Verify resource status in database is 'assigned'
    db_res = await test_db["resources"].find_one({"_id": ObjectId(res_id)})
    assert db_res["status"] == ResourceStatus.ASSIGNED

    # 2. Transition assignment to en_route
    resp_enroute = await async_client.patch(
        f"/api/assignments/{asg_id}/status",
        json={"status": "en_route"},
    )
    assert resp_enroute.status_code == 200
    assert resp_enroute.json()["status"] == "en_route"

    db_res = await test_db["resources"].find_one({"_id": ObjectId(res_id)})
    assert db_res["status"] == ResourceStatus.EN_ROUTE

    db_inc = await test_db["incidents"].find_one({"_id": ObjectId(inc_id)})
    assert db_inc["status"] == IncidentStatus.EN_ROUTE

    # 3. Transition assignment to on_scene
    resp_onscene = await async_client.patch(
        f"/api/assignments/{asg_id}/status",
        json={"status": "on_scene"},
    )
    assert resp_onscene.status_code == 200
    assert resp_onscene.json()["status"] == "on_scene"

    db_res = await test_db["resources"].find_one({"_id": ObjectId(res_id)})
    assert db_res["status"] == ResourceStatus.ON_SCENE

    db_inc = await test_db["incidents"].find_one({"_id": ObjectId(inc_id)})
    assert db_inc["status"] == IncidentStatus.ON_SCENE

    # 4. Transition assignment to completed
    resp_comp = await async_client.patch(
        f"/api/assignments/{asg_id}/status",
        json={"status": "completed"},
    )
    assert resp_comp.status_code == 200
    assert resp_comp.json()["status"] == "completed"

    # Completing assignment frees the resource to 'available'
    db_res = await test_db["resources"].find_one({"_id": ObjectId(res_id)})
    assert db_res["status"] == ResourceStatus.AVAILABLE

    # Incident does NOT auto-resolve on assignment complete
    db_inc = await test_db["incidents"].find_one({"_id": ObjectId(inc_id)})
    assert db_inc["status"] == IncidentStatus.ON_SCENE


@pytest.mark.asyncio
async def test_concurrency_race_for_same_resource(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """
    Verify concurrency safety: when two dispatch requests race simultaneously
    for the exact same available unit, only one succeeds and no double-dispatch occurs.
    """
    # Create single dedicated test resource
    res_oid = ObjectId()
    now = datetime.now(timezone.utc)
    await test_db["resources"].insert_one({
        "_id": res_oid,
        "name": "Race Ambulance 007",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "location": {"type": "Point", "coordinates": [72.5650, 23.0140]},
        "capacity": 4,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Paldi Station",
        "updated_at": now,
    })

    # Create two separate incidents
    r1 = await async_client.post(
        "/api/reports",
        json={"source": "citizen", "text": "Crash incident 1", "lat": 23.0140, "lng": 72.5650},
    )
    r2 = await async_client.post(
        "/api/reports",
        json={"source": "citizen", "text": "Medical emergency 2", "lat": 23.0140, "lng": 72.5650},
    )
    inc1_id = r1.json()["incident_id"]
    inc2_id = r2.json()["incident_id"]

    res_str = str(res_oid)

    # Fire two concurrent dispatch requests for the exact same resource
    task1 = async_client.post(f"/api/incidents/{inc1_id}/dispatch", json={"resource_ids": [res_str]})
    task2 = async_client.post(f"/api/incidents/{inc2_id}/dispatch", json={"resource_ids": [res_str]})

    resp1, resp2 = await asyncio.gather(task1, task2)

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    data1 = resp1.json()
    data2 = resp2.json()

    # Exactly one succeeded and one skipped
    success1 = len(data1["assignments"]) == 1 and res_str not in data1["skipped"]
    success2 = len(data2["assignments"]) == 1 and res_str not in data2["skipped"]

    assert success1 != success2, "Expected exactly one dispatch to win the race!"

    # Verify only one assignment exists in database for this resource
    asg_count = await test_db["assignments"].count_documents({"resource_id": res_oid})
    assert asg_count == 1
