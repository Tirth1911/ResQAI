import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.database import DatabaseManager
from backend.app.services.assist import generate_incident_assistance, get_overall_briefing


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    DatabaseManager.client = None
    DatabaseManager.db = None
    db = await DatabaseManager.connect_to_mongo()
    await db.incidents.delete_many({})
    await db.resources.delete_many({})


@pytest.mark.asyncio
async def test_ai_assistance_generation_fallback_path():
    db_inst = DatabaseManager.get_db()
    test_inc = {
        "_id": "507f1f77bcf86cd799439011",
        "incident_id": "INC-ASSIST-01",
        "type": "fire",
        "severity": "critical",
        "title": "Major industrial fire at storage facility",
        "description": "Chemical fire spreading with heavy black smoke",
        "address": "456 Industrial Way",
        "reports": [{"source": "call_911", "text": "Chemical fire spreading with heavy black smoke"}]
    }

    res = await generate_incident_assistance(db_inst, test_inc)
    assert res is not None
    assert "summary" in res
    assert "assessment" in res
    assert "recommended_actions" in res
    assert len(res["recommended_actions"]) <= 5
    assert "field_guidance" in res
    assert len(res["field_guidance"]) <= 4
    assert res["generated_by"] in ["rules", "llm"]


@pytest.mark.asyncio
async def test_overall_briefing_aggregation():
    db_inst = DatabaseManager.get_db()
    briefing = await get_overall_briefing(db_inst)
    assert "total_active_incidents" in briefing
    assert "severity_counts" in briefing
    assert "briefing_narrative" in briefing


@pytest.mark.asyncio
async def test_assist_and_briefing_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create incident
        r1 = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Flash flood submerging main street bridge",
            "lat": 37.75,
            "lng": -122.40
        })
        assert r1.status_code == 201
        inc_id = r1.json()["incident_id"]

        # POST trigger assist
        assist_post = await ac.post(f"/api/incidents/{inc_id}/assist")
        assert assist_post.status_code == 200
        a_data = assist_post.json()
        assert "recommended_actions" in a_data

        # GET assist
        assist_get = await ac.get(f"/api/incidents/{inc_id}/assist")
        assert assist_get.status_code == 200
        assert assist_get.json()["summary"] == a_data["summary"]

        # GET briefing
        brief_res = await ac.get("/api/briefing")
        assert brief_res.status_code == 200
        b_data = brief_res.json()
        assert "briefing_narrative" in b_data
        assert b_data["total_active_incidents"] >= 1
