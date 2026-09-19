import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database import DatabaseManager


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Ensure MongoDB client binds to the current test event loop."""
    DatabaseManager.client = None
    DatabaseManager.db = None
    await DatabaseManager.connect_to_mongo()


@pytest.mark.asyncio
async def test_post_reports_all_six_sources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        sources = [
            ("call_911", {"text": "Structural fire reported at main street apartment", "lat": 37.7749, "lng": -122.4194}),
            ("iot_sensor", {"text": "", "lat": 37.7750, "lng": -122.4190, "extra": {"sensor": "smoke", "value": 850, "unit": "ppm"}}),
            ("hospital", {"text": "Emergency ER overflow", "lat": 37.7755, "lng": -122.4180, "extra": {"casualty_count": 12, "beds_needed": 5}}),
            ("citizen", {"text": "Citizen report of fallen tree blocking intersection", "lat": 37.7760, "lng": -122.4170}),
            ("social_media", {"text": "Social post about localized flash flood near station", "lat": 37.7770, "lng": -122.4160}),
            ("field_unit", {"text": "Police unit requesting back-up for traffic control", "lat": 37.7780, "lng": -122.4150}),
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
            assert inc["status"] == "new"
            assert inc["type"] == "other"
            assert inc["severity"] == "medium"

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

        # 2. Transition new -> triaged (valid)
        t1 = await ac.patch(f"/api/incidents/{inc_id}/status", json={"status": "triaged"})
        assert t1.status_code == 200
        assert t1.json()["status"] == "triaged"

        # 3. Transition triaged -> en_route (invalid transition: triaged can go to dispatched or resolved)
        t_invalid = await ac.patch(f"/api/incidents/{inc_id}/status", json={"status": "en_route"})
        assert t_invalid.status_code == 400
        assert "Invalid status transition" in t_invalid.json()["detail"]

        # 4. Transition triaged -> dispatched (valid)
        t2 = await ac.patch(f"/api/incidents/{inc_id}/status", json={"status": "dispatched"})
        assert t2.status_code == 200
        assert t2.json()["status"] == "dispatched"

        # 5. Transition dispatched -> resolved (valid resolution from active state)
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
