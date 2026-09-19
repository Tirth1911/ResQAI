import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database import DatabaseManager


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    DatabaseManager.client = None
    DatabaseManager.db = None
    db = await DatabaseManager.connect_to_mongo()
    await db.incidents.delete_many({})
    await db.resources.delete_many({})
    await db.assignments.delete_many({})

    # Seed test resources
    test_resources = [
        {
            "resource_id": "RES-TEST-01",
            "name": "Fire Engine 1",
            "kind": "fire_truck",
            "category": "FIRE_TRUCK",
            "status": "available",
            "location": {"type": "Point", "coordinates": [-122.4194, 37.7749]},
            "capabilities": ["firefighting", "rescue"]
        },
        {
            "resource_id": "RES-TEST-02",
            "name": "Fire Engine 2",
            "kind": "fire_truck",
            "category": "FIRE_TRUCK",
            "status": "available",
            "location": {"type": "Point", "coordinates": [-122.4000, 37.7800]},
            "capabilities": ["firefighting"]
        },
        {
            "resource_id": "RES-TEST-BUSY",
            "name": "Fire Engine Busy",
            "kind": "fire_truck",
            "category": "FIRE_TRUCK",
            "status": "busy",
            "location": {"type": "Point", "coordinates": [-122.4190, 37.7750]},
            "capabilities": ["firefighting"]
        },
        {
            "resource_id": "RES-TEST-AMB",
            "name": "Medic Ambulance 1",
            "kind": "ambulance",
            "category": "AMBULANCE",
            "status": "available",
            "location": {"type": "Point", "coordinates": [-122.4180, 37.7760]},
            "capabilities": ["medical"]
        }
    ]
    await db.resources.insert_many(test_resources)


@pytest.mark.asyncio
async def test_recommendations_distance_ordering_and_busy_exclusion():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a fire incident
        r1 = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Building fire blazes near downtown center",
            "lat": 37.7749,
            "lng": -122.4194
        })
        inc_id = r1.json()["incident_id"]

        # GET recommendations
        rec_res = await ac.get(f"/api/incidents/{inc_id}/recommendations")
        assert rec_res.status_code == 200
        recs = rec_res.json()
        assert "units" in recs
        units = recs["units"]

        # Ensure busy unit is excluded
        rec_ids = [u["resource_id"] for u in units]
        assert "RES-TEST-BUSY" not in rec_ids

        # Ensure RES-TEST-01 (closest fire truck) is ranked #1
        assert len(units) >= 1
        assert units[0]["resource_id"] == "RES-TEST-01"
        assert "reason" in units[0]


@pytest.mark.asyncio
async def test_dispatch_state_sync_and_assignment_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Medical emergency on main street",
            "lat": 37.7749,
            "lng": -122.4194
        })
        inc_id = r1.json()["incident_id"]

        # Dispatch RES-TEST-AMB
        disp_res = await ac.post(f"/api/incidents/{inc_id}/dispatch", json={"resource_ids": ["RES-TEST-AMB"]})
        assert disp_res.status_code == 200
        disp_data = disp_res.json()
        assert len(disp_data["dispatched"]) == 1
        assert disp_data["incident"]["status"] == "dispatched"

        # Check assignment exists
        inc_detail = await ac.get(f"/api/incidents/{inc_id}")
        asgns = inc_detail.json()["assignments"]
        assert len(asgns) == 1
        asgn_id = asgns[0]["id"]

        # PATCH assignment status to en_route
        p1 = await ac.patch(f"/api/assignments/{asgn_id}/status", json={"status": "en_route"})
        assert p1.status_code == 200
        assert p1.json()["status"] == "en_route"

        inc_detail_p1 = await ac.get(f"/api/incidents/{inc_id}")
        assert inc_detail_p1.json()["status"] == "en_route"

        # PATCH assignment status to completed (frees resource)
        p2 = await ac.patch(f"/api/assignments/{asgn_id}/status", json={"status": "completed"})
        assert p2.status_code == 200
        assert p2.json()["completed"] is True

        res_check = await ac.get("/api/resources?kind=ambulance")
        assert res_check.json()[0]["status"] == "available"


@pytest.mark.asyncio
async def test_concurrency_race_for_same_resource():
    transport = ASGITransport(app=app)

    async def call_dispatch():
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/api/reports", json={
                "source": "call_911",
                "text": "Fire incident for race test",
                "lat": 37.70,
                "lng": -122.40
            })
            inc_id = r.json()["incident_id"]
            return await ac.post(f"/api/incidents/{inc_id}/dispatch", json={"resource_ids": ["RES-TEST-02"]})

    # Execute two dispatch requests in parallel for the exact same unit RES-TEST-02
    res1, res2 = await asyncio.gather(call_dispatch(), call_dispatch())

    d1 = res1.json()
    d2 = res2.json()

    dispatched_count1 = len(d1.get("dispatched", []))
    dispatched_count2 = len(d2.get("dispatched", []))

    # Exactly one dispatch call succeeds in claiming RES-TEST-02, the other receives unclaimed
    assert dispatched_count1 + dispatched_count2 == 1
