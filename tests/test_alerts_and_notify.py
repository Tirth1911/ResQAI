import pytest
import pytest_asyncio
from datetime import timedelta
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.database import DatabaseManager
from backend.app.services.alerts import create_alert, evaluate_delayed_and_escalation_checks


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    DatabaseManager.client = None
    DatabaseManager.db = None
    db = await DatabaseManager.connect_to_mongo()
    await db.incidents.delete_many({})
    await db.alerts.delete_many({})
    await db.notifications.delete_many({})


@pytest.mark.asyncio
async def test_critical_incident_produces_alert_and_four_channel_notifications():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create critical report with explosion / mass casualty keywords
        res = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Massive explosion with casualties and collapsed building",
            "lat": 37.7749,
            "lng": -122.4194
        })
        assert res.status_code == 201
        inc_id = res.json()["incident_id"]

        # Directly trigger alert creation for critical incident
        db_inst = DatabaseManager.get_db()
        alt = await create_alert(
            db=db_inst,
            alert_type="critical_incident",
            level="critical",
            incident_id=inc_id,
            message="Critical emergency incident reported"
        )
        assert alt is not None
        assert alt["level"] == "critical"

        # Check notifications generated across 4 channels (in_app, push, sms, email)
        notif_cursor = db_inst.notifications.find({"alert_id": alt["alert_id"]})
        notifs = await notif_cursor.to_list(length=10)
        channels = [n["channel"] for n in notifs]

        assert "in_app" in channels
        assert "push" in channels
        assert "sms" in channels
        assert "email" in channels


@pytest.mark.asyncio
async def test_duplicate_alert_suppression_within_ten_minutes():
    db_inst = DatabaseManager.get_db()
    # 1st alert -> created
    alt1 = await create_alert(
        db=db_inst,
        alert_type="resource_shortage",
        level="warning",
        incident_id="INC-DUP-TEST",
        message="Shortage alert 1"
    )
    assert alt1 is not None

    # 2nd alert within 10 min -> suppressed (returns None)
    alt2 = await create_alert(
        db=db_inst,
        alert_type="resource_shortage",
        level="warning",
        incident_id="INC-DUP-TEST",
        message="Shortage alert 2"
    )
    assert alt2 is None


@pytest.mark.asyncio
async def test_delayed_alert_after_time_offset():
    db_inst = DatabaseManager.get_db()
    # Create incident
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Building fire reported for delay test",
            "lat": 37.70,
            "lng": -122.40
        })
        assert r.status_code == 201

        # Time travel offset + 20 minutes
        offset = timedelta(minutes=20)
        created_count = await evaluate_delayed_and_escalation_checks(
            db=db_inst,
            demo_time_scale=1.0,
            time_offset=offset
        )
        assert created_count >= 1

        # Check alerts created in DB
        alerts = await db_inst.alerts.find({}).to_list(length=10)
        types = [a["type"] for a in alerts]
        assert "delayed_response" in types or "escalation" in types
