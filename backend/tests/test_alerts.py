from datetime import datetime, timedelta, timezone
from bson import ObjectId
import pytest
from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase
from starlette.testclient import TestClient

from app.config import settings
from app.main import app
from app.models import (
    AlertLevel,
    AlertType,
    IncidentSeverity,
    IncidentStatus,
    NotificationChannel,
)
from app.services.alerts import create_alert, run_alert_checks


@pytest.mark.asyncio
async def test_critical_incident_produces_alert_and_4_channel_notifications(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """
    Verify that an incoming critical incident triggers:
    1. A critical_incident alert with level=critical.
    2. Four notifications across channels: in_app, push, sms, email.
    """
    resp = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Massive explosion with multiple casualties trapped in chemical plant blaze.",
            "lat": 23.0780,
            "lng": 72.6710,
        },
    )
    assert resp.status_code == 201
    inc_id = resp.json()["incident_id"]
    inc_oid = ObjectId(inc_id)

    # 1. Verify Alert document created
    alert_doc = await test_db["alerts"].find_one({
        "incident_id": inc_oid,
        "type": AlertType.CRITICAL_INCIDENT,
    })
    assert alert_doc is not None
    assert alert_doc["level"] == AlertLevel.CRITICAL
    assert alert_doc["acknowledged"] is False

    # 2. Verify 4 Notifications created across all required channels
    cursor = test_db["notifications"].find({"alert_id": alert_doc["_id"]})
    notifications = [n async for n in cursor]
    assert len(notifications) == 4

    channels = {n["channel"] for n in notifications}
    assert channels == {
        NotificationChannel.IN_APP,
        NotificationChannel.PUSH,
        NotificationChannel.SMS,
        NotificationChannel.EMAIL,
    }

    # Verify recipients
    email_notif = next(n for n in notifications if n["channel"] == NotificationChannel.EMAIL)
    assert "duty.officer@resqai.demo" in email_notif["recipient"]

    # 3. Verify GET /api/alerts and GET /api/notifications
    alerts_resp = await async_client.get("/api/alerts")
    assert alerts_resp.status_code == 200
    alert_ids = [a["id"] for a in alerts_resp.json()]
    assert str(alert_doc["_id"]) in alert_ids

    notifs_resp = await async_client.get("/api/notifications")
    assert notifs_resp.status_code == 200
    assert len(notifs_resp.json()) >= 4


@pytest.mark.asyncio
async def test_duplicate_alert_suppression(test_db: AsyncDatabase):
    """Verify that identical alert types for the same incident within 10 min are suppressed."""
    inc_oid = ObjectId()
    now = datetime.now(timezone.utc)

    # First alert should succeed
    a1 = await create_alert(
        test_db,
        type=AlertType.CRITICAL_INCIDENT,
        level=AlertLevel.CRITICAL,
        incident_id=inc_oid,
        message="Alert trigger 1",
        now=now,
    )
    assert a1 is not None

    # Duplicate alert within 10 minutes must be suppressed
    a2 = await create_alert(
        test_db,
        type=AlertType.CRITICAL_INCIDENT,
        level=AlertLevel.CRITICAL,
        incident_id=inc_oid,
        message="Alert trigger 2 (duplicate)",
        now=now + timedelta(minutes=4),
    )
    assert a2 is None

    count = await test_db["alerts"].count_documents({
        "incident_id": inc_oid,
        "type": AlertType.CRITICAL_INCIDENT,
    })
    assert count == 1

    # Alert after 11 minutes should be allowed
    a3 = await create_alert(
        test_db,
        type=AlertType.CRITICAL_INCIDENT,
        level=AlertLevel.CRITICAL,
        incident_id=inc_oid,
        message="Alert trigger 3 (after suppression window)",
        now=now + timedelta(minutes=11),
    )
    assert a3 is not None
    count_after = await test_db["alerts"].count_documents({
        "incident_id": inc_oid,
        "type": AlertType.CRITICAL_INCIDENT,
    })
    assert count_after == 2


@pytest.mark.asyncio
async def test_delayed_response_and_escalation_after_time_travel(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """
    Verify time-travel checks:
    - Incident > 10 min without on_scene -> delayed_response alert
    - Incident > 20 min without on_scene -> escalation alert
    """
    t0 = datetime.now(timezone.utc)
    inc_oid = ObjectId()

    await test_db["incidents"].insert_one({
        "_id": inc_oid,
        "title": "Simulated Delayed Incident",
        "description": "Traffic junction blockage.",
        "type": "accident",
        "severity": IncidentSeverity.MEDIUM,
        "priority": 3,
        "status": IncidentStatus.TRIAGED,
        "source": "citizen",
        "location": {"type": "Point", "coordinates": [72.5714, 23.0225]},
        "created_at": t0,
        "updated_at": t0,
    })

    # 1. At t0 + 2 min: no alerts for this incident
    alerts_t2 = await run_alert_checks(test_db, now=t0 + timedelta(minutes=2))
    assert not any(a["incident_id"] == inc_oid for a in alerts_t2)

    # 2. At t0 + 12 min (> 10 min): delayed_response alert triggers for this incident
    alerts_t12 = await run_alert_checks(test_db, now=t0 + timedelta(minutes=12))
    assert any(a["type"] == AlertType.DELAYED_RESPONSE and a["incident_id"] == inc_oid for a in alerts_t12)

    # 3. At t0 + 22 min (> 20 min): escalation alert triggers for this incident
    alerts_t22 = await run_alert_checks(test_db, now=t0 + timedelta(minutes=22))
    assert any(a["type"] == AlertType.ESCALATION and a["incident_id"] == inc_oid for a in alerts_t22)


@pytest.mark.asyncio
async def test_alert_ack_endpoint(async_client: AsyncClient, test_db: AsyncDatabase):
    """Verify POST /api/alerts/{id}/ack marks alert acknowledged."""
    inc_oid = ObjectId()
    alert_doc = await create_alert(
        test_db,
        type=AlertType.CRITICAL_INCIDENT,
        level=AlertLevel.CRITICAL,
        incident_id=inc_oid,
        message="Critical event for acknowledgment testing",
    )
    alert_id = str(alert_doc["_id"])

    # Acknowledge alert
    ack_resp = await async_client.post(f"/api/alerts/{alert_id}/ack")
    assert ack_resp.status_code == 200
    assert ack_resp.json()["acknowledged"] is True

    # Filter acknowledged in list
    unack_resp = await async_client.get("/api/alerts?acknowledged=false")
    assert unack_resp.status_code == 200
    assert all(a["id"] != alert_id for a in unack_resp.json())


@pytest.mark.asyncio
async def test_dev_tick_endpoint(async_client: AsyncClient, monkeypatch):
    """Verify POST /api/dev/tick endpoint functions when DEMO_MODE=true."""
    # When DEMO_MODE=False, returns 403
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    forbidden_resp = await async_client.post("/api/dev/tick")
    assert forbidden_resp.status_code == 403

    # When DEMO_MODE=True, returns 200
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    ok_resp = await async_client.post("/api/dev/tick")
    assert ok_resp.status_code == 200
    assert ok_resp.json()["status"] == "ok"


def test_websocket_realtime_hello():
    """Verify native WebSocket /ws connection handshake and hello message."""
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "connected"
        assert "ResQAI Realtime Gateway Connected" in data["data"]["message"]
        assert "ts" in data
