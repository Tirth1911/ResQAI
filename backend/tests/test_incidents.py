from datetime import datetime, timezone
import pytest
from bson import ObjectId
from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.models import (
    AssignmentStatus,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ReportSource,
    ResourceKind,
    ResourceStatus,
)


@pytest.mark.asyncio
async def test_report_ingestion_all_sources(async_client: AsyncClient, test_db: AsyncDatabase):
    """Verify report ingestion across all 6 domain report sources."""
    sources_payloads = [
        {
            "source": ReportSource.CITIZEN,
            "reporter": "Ramesh Patel",
            "text": "Thick smoke visible from warehouse roof near SG Highway.",
            "lat": 23.0315,
            "lng": 72.5580,
            "address": "SG Highway, Bodakdev",
        },
        {
            "source": ReportSource.CALL_CENTER,
            "reporter": "Operator #412",
            "text": "Caller reports head-on two vehicle crash at crossroad.",
            "lat": 23.0285,
            "lng": 72.5070,
            "address": "Iscon Cross Road",
        },
        {
            "source": ReportSource.IOT_SENSOR,
            "reporter": "IoT-Node-88",
            "text": "Perimeter alarm active",
            "lat": 23.0780,
            "lng": 72.6710,
            "address": "Naroda Industrial Area Phase 2",
            "extra": {"sensor": "smoke", "value": 870, "unit": "ppm"},
        },
        {
            "source": ReportSource.FIELD_TEAM,
            "reporter": "Officer Dave",
            "text": "On-scene initial assessment confirms underpass water level rising.",
            "lat": 23.0110,
            "lng": 72.5540,
            "address": "Parimal Underpass",
        },
        {
            "source": ReportSource.HOSPITAL,
            "reporter": "Triage Desk Civil",
            "text": "Emergency ward overflow.",
            "lat": 23.0528,
            "lng": 72.6035,
            "address": "Civil Hospital Asarwa",
            "extra": {"incoming_casualties": 15, "beds_available": 0},
        },
        {
            "source": ReportSource.GOVERNMENT,
            "reporter": "SEOC Gandhinagar",
            "text": "Weather bureau red alert warning for severe thunder squalls.",
            "lat": 23.2180,
            "lng": 72.6510,
            "address": "Gandhinagar SEOC",
        },
    ]

    for payload in sources_payloads:
        resp = await async_client.post("/api/reports", json=payload)
        assert resp.status_code == 201, f"Failed for source {payload['source']}: {resp.text}"
        data = resp.json()
        assert "incident_id" in data
        assert data["merged"] is False
        assert "incident" in data

        inc = data["incident"]
        assert inc["source"] == payload["source"]
        assert inc["lat"] == payload["lat"]
        assert inc["lng"] == payload["lng"]
        assert len(inc["reports"]) == 1
        assert inc["reports"][0]["lat"] == payload["lat"]
        assert inc["reports"][0]["lng"] == payload["lng"]

        # Check source-specific normalizations
        if payload["source"] == ReportSource.IOT_SENSOR:
            assert "smoke" in inc["description"]
            assert "870 ppm" in inc["description"]
        elif payload["source"] == ReportSource.HOSPITAL:
            assert "15" in inc["description"]
            assert "shortage" in inc["description"].lower()


@pytest.mark.asyncio
async def test_invalid_and_missing_id_handling(async_client: AsyncClient):
    """Verify invalid format and missing ObjectIds return 404 cleanly, never 500."""
    # Malformed IDs
    malformed_ids = ["not-an-id", "12345", "xyz_invalid", "null", "undefined"]
    for bad_id in malformed_ids:
        resp = await async_client.get(f"/api/incidents/{bad_id}")
        assert resp.status_code == 404, f"Expected 404 for {bad_id}, got {resp.status_code}"

        patch_resp = await async_client.patch(
            f"/api/incidents/{bad_id}/status",
            json={"status": "triaged"},
        )
        assert patch_resp.status_code == 404, f"Expected 404 on patch for {bad_id}"

    # Valid format, non-existent ObjectId
    non_existent_id = str(ObjectId())
    resp = await async_client.get(f"/api/incidents/{non_existent_id}")
    assert resp.status_code == 404

    patch_resp = await async_client.patch(
        f"/api/incidents/{non_existent_id}/status",
        json={"status": "triaged"},
    )
    assert patch_resp.status_code == 404


@pytest.mark.asyncio
async def test_status_transitions_and_resource_freeing(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """
    Verify status transition validation rules:
    - Linear progression: new -> triaged -> dispatched -> en_route -> on_scene -> resolved
    - Resolve allowed from any active state
    - Invalid reverse/skip transitions rejected with 400
    - Resolving frees assigned resources
    """
    # 1. Create a fresh incident
    create_resp = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Factory chemical smoke spreading.",
            "lat": 23.0720,
            "lng": 72.6640,
        },
    )
    assert create_resp.status_code == 201
    inc_id = create_resp.json()["incident_id"]

    # Test invalid skip transition from 'new' to 'on_scene'
    skip_resp = await async_client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "on_scene"},
    )
    assert skip_resp.status_code == 400
    assert "Invalid status transition" in skip_resp.json()["detail"]

    # Test valid step: new -> triaged
    resp1 = await async_client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "triaged"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "triaged"

    # Test valid step: triaged -> dispatched
    resp2 = await async_client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "dispatched"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "dispatched"

    # Simulate an assigned resource
    res_oid = ObjectId()
    now = datetime.now(timezone.utc)
    await test_db["resources"].insert_one({
        "_id": res_oid,
        "name": "Test Response Engine 99",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.ASSIGNED,
        "location": {"type": "Point", "coordinates": [72.6640, 23.0720]},
        "capacity": 6,
        "capabilities": ["fire", "industrial"],
        "station": "Naroda GIDC",
        "updated_at": now,
    })

    asg_oid = ObjectId()
    await test_db["assignments"].insert_one({
        "_id": asg_oid,
        "incident_id": ObjectId(inc_id),
        "resource_id": res_oid,
        "status": AssignmentStatus.ASSIGNED,
        "score": 0.95,
        "distance_km": 1.2,
        "eta_min": 4.0,
        "assigned_at": now,
        "updated_at": now,
        "completed_at": None,
    })

    # Test GET incident detail including joined assignments
    detail_resp = await async_client.get(f"/api/incidents/{inc_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert len(detail_data["assignments"]) == 1
    assert detail_data["assignments"][0]["resource"]["name"] == "Test Response Engine 99"

    # Test resolving from dispatched (resolve from active state allowed)
    resolve_resp = await async_client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "resolved"},
    )
    assert resolve_resp.status_code == 200
    resolved_data = resolve_resp.json()
    assert resolved_data["status"] == "resolved"
    assert resolved_data["resolved_at"] is not None

    # Verify resource was freed back to 'available'
    freed_res = await test_db["resources"].find_one({"_id": res_oid})
    assert freed_res["status"] == ResourceStatus.AVAILABLE

    # Verify assignment was marked 'completed'
    completed_asg = await test_db["assignments"].find_one({"_id": asg_oid})
    assert completed_asg["status"] == AssignmentStatus.COMPLETED
    assert completed_asg["completed_at"] is not None

    # Test invalid transition once resolved
    reopen_resp = await async_client.patch(
        f"/api/incidents/{inc_id}/status",
        json={"status": "triaged"},
    )
    assert reopen_resp.status_code == 400


@pytest.mark.asyncio
async def test_list_incidents_and_resources_endpoints(
    async_client: AsyncClient,
    test_db: AsyncDatabase,
):
    """Verify GET /api/incidents and GET /api/resources with query filters."""
    # List incidents
    inc_resp = await async_client.get("/api/incidents?active_only=true")
    assert inc_resp.status_code == 200
    active_list = inc_resp.json()
    assert all(i["status"] != "resolved" for i in active_list)

    # List resources
    res_resp = await async_client.get("/api/resources?kind=fire_truck")
    assert res_resp.status_code == 200
    resources = res_resp.json()
    assert len(resources) >= 1
    for r in resources:
        assert r["kind"] == "fire_truck"
        assert "lat" in r and "lng" in r
