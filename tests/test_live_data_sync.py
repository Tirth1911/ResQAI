import pytest
import pytest_asyncio
import json
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.database import DatabaseManager


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    DatabaseManager.client = None
    DatabaseManager.db = None
    db = await DatabaseManager.connect_to_mongo()
    # Seed a test resource
    await db.resources.delete_many({"resource_id": "RES-TEST-FIRE-01"})
    await db.resources.insert_one({
        "resource_id": "RES-TEST-FIRE-01",
        "name": "Test Fire Tender 01",
        "category": "FIRE_TRUCK",
        "capabilities": ["FIRE", "WATER_TENDER"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [72.585, 23.033]},
        "capacity": 4
    })


def test_websocket_realtime_events_flow():
    """Verify live synchronization via WebSocket."""
    client = TestClient(app)

    with client.websocket_connect("/ws/dashboard") as ws:
        # 1. Initial Handshake CONNECTED packet
        handshake_raw = ws.receive_text()
        handshake = json.loads(handshake_raw)
        assert handshake["event"] == "CONNECTED"
        assert "event_id" in handshake

        # 2. Trigger Server Simulation
        sim_resp = client.post("/api/simulation/simulate-critical")
        assert sim_resp.status_code == 200
        sim_data = sim_resp.json()
        assert sim_data["status"] == "success"
        created_inc = sim_data["incident"]
        inc_id = created_inc["incident_id"]

        # Collect events emitted over WebSocket
        received_events = []
        for _ in range(4):
            packet_raw = ws.receive_text()
            pkt = json.loads(packet_raw)
            received_events.append(pkt)

        event_names = [p["event"] for p in received_events]
        assert "NEW_INCIDENT" in event_names or "INCIDENT_CREATED" in event_names
        assert "DISPATCH_REQUIRED" in event_names
        assert "ALERT_CREATED" in event_names

        # Verify event envelope fields
        for pkt in received_events:
            assert "event_id" in pkt
            assert pkt["event_id"].startswith("evt_")
            assert "timestamp" in pkt

        # 3. Dispatch / Assign Resource
        assign_resp = client.post(
            f"/api/incidents/{inc_id}/assign-resource",
            json={
                "resource_id": "RES-TEST-FIRE-01",
                "actor": "Command Dispatcher",
                "notes": "Dispatched to test incident"
            }
        )
        assert assign_resp.status_code == 200

        # Receive dispatch events
        dispatch_packets = []
        for _ in range(4):  # RESOURCE_DISPATCHED, RESOURCE_ASSIGNED, RESOURCE_UPDATED, INCIDENT_UPDATED
            pkt = json.loads(ws.receive_text())
            dispatch_packets.append(pkt)

        d_events = [p["event"] for p in dispatch_packets]
        assert "RESOURCE_DISPATCHED" in d_events or "RESOURCE_ASSIGNED" in d_events
        assert "INCIDENT_UPDATED" in d_events

        # 4. Resolve Incident
        resolve_resp = client.post(
            f"/api/incidents/{inc_id}/resolve",
            json={
                "actor": "Command Dispatcher",
                "notes": "Incident contained and secured"
            }
        )
        assert resolve_resp.status_code == 200
        resolved_data = resolve_resp.json()
        assert resolved_data["status"] == "RESOLVED"

        # Receive resolve events
        resolve_packets = []
        for _ in range(2):  # INCIDENT_RESOLVED, INCIDENT_UPDATED
            pkt = json.loads(ws.receive_text())
            resolve_packets.append(pkt)

        r_events = [p["event"] for p in resolve_packets]
        assert "INCIDENT_RESOLVED" in r_events
