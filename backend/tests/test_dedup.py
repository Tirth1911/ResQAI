from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.services.geo import haversine_km


def test_haversine_calculation():
    """Verify haversine formula against known coordinates."""
    # Ahmedabad center to Gandhinagar center (~22-24 km)
    dist = haversine_km(23.0225, 72.5714, 23.2156, 72.6369)
    assert 21.0 <= dist <= 25.0

    # Distance to identical coordinate is zero
    assert haversine_km(23.0225, 72.5714, 23.0225, 72.5714) == 0.0

    # 300 meters check
    small_dist = haversine_km(23.0315, 72.5580, 23.0335, 72.5595)
    assert 0.20 <= small_dist <= 0.35


@pytest.mark.asyncio
async def test_same_fire_within_300m_and_10min_merges(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify duplicate reports within 300m and 10min merge into the original incident."""
    now = datetime.now(timezone.utc)
    t1 = now - timedelta(minutes=5)

    # 1. First caller
    resp1 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "reporter": "Caller A",
            "text": "Huge fire and thick black smoke burning in restaurant kitchen near CG Road.",
            "lat": 23.0315,
            "lng": 72.5580,
            "address": "CG Road, Navrangpura",
            "reported_at": t1.isoformat(),
        },
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["merged"] is False
    inc_id = data1["incident_id"]

    # 2. Second caller (~280 meters away, 5 mins later, different wording)
    resp2 = await async_client.post(
        "/api/reports",
        json={
            "source": "call_center",
            "reporter": "Operator #9",
            "text": "Flames and blaze seen rising from restaurant kitchen near CG Road.",
            "lat": 23.0335,
            "lng": 72.5595,
            "address": "Opposite CG Road Commercial Hub",
            "reported_at": now.isoformat(),
        },
    )
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["merged"] is True
    assert data2["incident_id"] == inc_id
    assert data2["duplicate_score"] is not None
    assert data2["duplicate_score"] > 0.4
    assert data2["incident"]["report_count"] == 2
    assert len(data2["incident"]["reports"]) == 2

    # 3. Test GET /api/incidents/{id}/reports
    reports_resp = await async_client.get(f"/api/incidents/{inc_id}/reports")
    assert reports_resp.status_code == 200
    reports = reports_resp.json()
    assert len(reports) == 2
    assert reports[0]["reporter"] == "Caller A"
    assert reports[1]["reporter"] == "Operator #9"


@pytest.mark.asyncio
async def test_same_text_5km_apart_does_not_merge(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify reports with identical text but 5 km apart do not merge."""
    now = datetime.now(timezone.utc)

    # First incident at Navrangpura
    resp1 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Major multi-vehicle collision with car overturned blocking traffic.",
            "lat": 23.0315,
            "lng": 72.5580,
            "reported_at": now.isoformat(),
        },
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["incident_id"]

    # Second incident ~5.5 km north at Chandkheda
    resp2 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Major multi-vehicle collision with car overturned blocking traffic.",
            "lat": 23.0815,
            "lng": 72.5580,
            "reported_at": now.isoformat(),
        },
    )
    assert resp2.status_code == 201
    id2 = resp2.json()["incident_id"]

    assert resp2.json()["merged"] is False
    assert id1 != id2


@pytest.mark.asyncio
async def test_same_location_2_hours_apart_does_not_merge(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify reports at the same location but > 45 minutes apart do not merge."""
    now = datetime.now(timezone.utc)
    t_old = now - timedelta(hours=2)

    # First report 2 hours ago
    resp1 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Flash flood waterlogging with underpass completely submerged.",
            "lat": 23.0110,
            "lng": 72.5540,
            "reported_at": t_old.isoformat(),
        },
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["incident_id"]

    # Second report now
    resp2 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Flash flood waterlogging with underpass completely submerged.",
            "lat": 23.0110,
            "lng": 72.5540,
            "reported_at": now.isoformat(),
        },
    )
    assert resp2.status_code == 201
    id2 = resp2.json()["incident_id"]

    assert resp2.json()["merged"] is False
    assert id1 != id2


@pytest.mark.asyncio
async def test_different_types_at_same_place_do_not_merge(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify different incident types at the exact same location do not merge."""
    now = datetime.now(timezone.utc)

    # Fire incident
    resp1 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Factory chemical boiler fire and flames spreading.",
            "lat": 23.0640,
            "lng": 72.6610,
            "reported_at": now.isoformat(),
        },
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["incident_id"]

    # Medical incident at the same place
    resp2 = await async_client.post(
        "/api/reports",
        json={
            "source": "hospital",
            "text": "Elderly patient collapsed with acute cardiac chest pain and bleeding.",
            "lat": 23.0640,
            "lng": 72.6610,
            "reported_at": now.isoformat(),
        },
    )
    assert resp2.status_code == 201
    id2 = resp2.json()["incident_id"]

    assert resp2.json()["merged"] is False
    assert id1 != id2


@pytest.mark.asyncio
async def test_third_report_bumps_severity(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify that when duplicate report_count reaches 3, severity is bumped by one level."""
    now = datetime.now(timezone.utc)
    lat, lng = 23.0500, 72.5400

    # 1. Report 1 (classified as fire with low/medium severity)
    r1 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Minor small spark and smoke burning in dry grass.",
            "lat": lat,
            "lng": lng,
            "reported_at": now.isoformat(),
        },
    )
    assert r1.status_code == 201
    inc1 = r1.json()["incident"]
    inc_id = r1.json()["incident_id"]
    initial_severity = inc1["severity"]
    initial_priority = inc1["priority"]
    assert inc1["report_count"] == 1

    # 2. Report 2 (merges, count=2, severity unchanged)
    r2 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Small smoke burning in dry grass nearby.",
            "lat": lat + 0.001,
            "lng": lng + 0.001,
            "reported_at": now.isoformat(),
        },
    )
    assert r2.status_code == 201
    data2 = r2.json()
    assert data2["merged"] is True
    assert data2["incident"]["report_count"] == 2
    assert data2["incident"]["severity"] == initial_severity

    # 3. Report 3 (merges, count=3, severity BUMPED by one level)
    r3 = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Grass smoke and burning fire seen by residents.",
            "lat": lat - 0.001,
            "lng": lng - 0.001,
            "reported_at": now.isoformat(),
        },
    )
    assert r3.status_code == 201
    data3 = r3.json()
    assert data3["merged"] is True
    assert data3["incident"]["report_count"] == 3

    bumped_severity = data3["incident"]["severity"]
    bumped_priority = data3["incident"]["priority"]

    # Severity must be higher (priority number lower)
    assert bumped_priority < initial_priority or bumped_severity == "critical"
