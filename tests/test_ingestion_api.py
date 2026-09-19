import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database import DatabaseManager


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Ensure MongoDB client binds to the current test event loop and clean test collections."""
    DatabaseManager.client = None
    DatabaseManager.db = None
    db = await DatabaseManager.connect_to_mongo()
    await db.incidents.delete_many({})
    await db.reports.delete_many({})


@pytest.mark.asyncio
async def test_post_reports_all_six_sources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        sources = [
            ("call_911", {"text": "Structural fire reported at main street apartment", "lat": 37.70, "lng": -122.40}),
            ("iot_sensor", {"text": "", "lat": 37.75, "lng": -122.35, "extra": {"sensor": "smoke", "value": 850, "unit": "ppm"}}),
            ("hospital", {"text": "Emergency ER overflow", "lat": 37.80, "lng": -122.30, "extra": {"casualty_count": 12, "beds_needed": 5}}),
            ("citizen", {"text": "Citizen report of fallen tree blocking intersection", "lat": 37.85, "lng": -122.25}),
            ("social_media", {"text": "Social post about localized flash flood near station", "lat": 37.90, "lng": -122.20}),
            ("field_unit", {"text": "Police unit requesting back-up for traffic control", "lat": 37.95, "lng": -122.15}),
        ]

        created_ids = []

        for source_name, payload in sources:
            req_body = {
                "source": source_name,
                "text": payload["text"],
                "lat": payload["lat"],
                "lng": payload["lng"],
                "address": "123 Test St",
                "extra": payload.get("extra")
            }

            response = await ac.post("/api/reports", json=req_body)
            assert response.status_code == 201, f"Failed for source {source_name}: {response.text}"
            data = response.json()

            assert "incident_id" in data
            assert data["merged"] is False
            assert "incident" in data

            inc = data["incident"]
            assert inc["source"] == source_name
            assert inc["status"] in ["new", "triaged"]

            created_ids.append(inc["id"])

        assert len(created_ids) == 6


@pytest.mark.asyncio
async def test_get_incidents_filter_and_active_only():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/incidents?active_only=true")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for inc in data:
            assert inc["status"].lower() not in ["resolved", "closed"]


@pytest.mark.asyncio
async def test_invalid_and_missing_id_handling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid ObjectId format
        res_invalid = await ac.get("/api/incidents/invalid-object-id-12345")
        assert res_invalid.status_code == 404
        assert "not found" in res_invalid.json()["detail"].lower()

        # Non-existent valid ObjectId format
        res_non_existent = await ac.get("/api/incidents/507f1f77bcf86cd799439011")
        assert res_non_existent.status_code == 404
        assert "not found" in res_non_existent.json()["detail"].lower()


@pytest.mark.asyncio
async def test_status_transitions_and_resolution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create report
        report_res = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Report for status transition testing",
            "lat": 37.77,
            "lng": -122.41
        })
        assert report_res.status_code == 201
        inc_id = report_res.json()["incident"]["id"]

        # 2. Transition new/triaged -> triaged/dispatched (valid)
        t1 = await ac.patch(f"/api/incidents/{inc_id}/status", json={"status": "dispatched"})
        assert t1.status_code == 200
        assert t1.json()["status"] == "dispatched"

        # 3. Transition dispatched -> resolved (valid resolution from active state)
        t3 = await ac.patch(f"/api/incidents/{inc_id}/status", json={"status": "resolved"})
        assert t3.status_code == 200
        data_resolved = t3.json()
        assert data_resolved["status"] == "resolved"
        assert data_resolved["resolved_at"] is not None


@pytest.mark.asyncio
async def test_get_resources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/resources")
        assert res.status_code == 200
        items = res.json()
        assert isinstance(items, list)
        for item in items:
            assert "lat" in item
            assert "lng" in item
