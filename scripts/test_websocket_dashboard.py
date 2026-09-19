import asyncio
import json
import os
import sys
from datetime import datetime, timezone

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from backend.app.database import DatabaseManager
from backend.app.websocket.manager import ws_manager, WebSocketEventType


def run_websocket_tests():
    print("=" * 75)
    print("🚀 ResQAI Real-Time WebSocket System Validation Suite")
    print("=" * 75)

    with TestClient(app) as client:
        # 1. TEST WS /ws/dashboard CONNECTION & HANDSHAKE
        print("\n[TEST 1/6] Connecting to WS /ws/dashboard...")
        with client.websocket_connect("/ws/dashboard") as websocket1:
            # Handshake
            handshake = websocket1.receive_json()
            print(f"  ✓ Handshake Received: event='{handshake.get('event')}', time='{handshake.get('timestamp')}'")
            assert handshake.get("event") == "CONNECTED", f"Expected CONNECTED, got {handshake}"

            # Ping/Pong Heartbeat
            websocket1.send_text("ping")
            pong = websocket1.receive_json()
            print(f"  ✓ Heartbeat Response: event='{pong.get('event')}', data={pong.get('data')}")
            assert pong.get("event") == "PONG", f"Expected PONG, got {pong}"

        print("  ✓ WebSocket disconnected gracefully. Active clients:", ws_manager.client_count)

        # 2. TEST MULTI-CLIENT BROADCAST (via REST alert trigger)
        print("\n[TEST 2/6] Testing Multi-Client WebSocket Broadcast...")
        with client.websocket_connect("/ws/dashboard") as ws1, client.websocket_connect("/ws/dashboard") as ws2:
            _ = ws1.receive_json() # Handshake
            _ = ws2.receive_json() # Handshake
            assert ws_manager.client_count == 2, f"Expected 2 active clients, got {ws_manager.client_count}"

            # Broadcast via REST endpoint
            alert_payload = {
                "title": "Severe Flood Alert Test",
                "message": "Water levels reaching orange warning marker.",
                "severity": "HIGH",
                "target_area": "Sector 4"
            }
            alert_res = client.post("/api/v1/alerts/", json=alert_payload)
            assert alert_res.status_code == 201

            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()

            assert msg1.get("event") == "NOTIFICATION_CREATED"
            assert msg2.get("event") == "NOTIFICATION_CREATED"
            print(f"  ✓ Both Dashboard Clients Received Standardized Event Envelope:")
            print(f"     Client 1: event='{msg1['event']}', timestamp='{msg1['timestamp']}'")
            print(f"     Client 2: event='{msg2['event']}', timestamp='{msg2['timestamp']}'")

        # 3. TEST INCIDENT_CREATED & INCIDENT_ESCALATED VIA REST API
        print("\n[TEST 3/6] Testing REST API Incident Creation -> WebSocket Broadcast...")
        with client.websocket_connect("/ws/dashboard") as ws:
            _ = ws.receive_json() # Handshake

            incident_payload = {
                "title": "Critical Flash Flood Inundation",
                "description": "Rapid water level rise near riverbank. 10 families stranded on rooftops.",
                "source": "citizen",
                "type": "flood",
                "severity": "CRITICAL",
                "priority": "P1",
                "location": {
                    "latitude": 22.3072,
                    "longitude": 73.1812,
                    "address": "Sayajiganj, Vadodara, Gujarat"
                }
            }

            # POST incident
            response = client.post("/api/v1/incidents/?auto_dedup=false", json=incident_payload)
            assert response.status_code == 201, f"Create incident failed: {response.text}"
            created_data = response.json()
            test_incident_id = created_data["incident_id"]
            print(f"  ✓ Incident Created via REST: {test_incident_id}")

            # Expect INCIDENT_CREATED event
            ws_msg1 = ws.receive_json()
            assert ws_msg1.get("event") == "INCIDENT_CREATED", f"Expected INCIDENT_CREATED, got {ws_msg1}"
            print(f"  ✓ WS Received: {ws_msg1.get('event')} for {ws_msg1.get('data', {}).get('incident_id')}")

            # Expect INCIDENT_ESCALATED event (because CRITICAL / P1)
            ws_msg2 = ws.receive_json()
            assert ws_msg2.get("event") == "INCIDENT_ESCALATED", f"Expected INCIDENT_ESCALATED, got {ws_msg2}"
            print(f"  ✓ WS Received: {ws_msg2.get('event')} for {ws_msg2.get('data', {}).get('incident_id')}")

            # 4. TEST RESOURCE_ASSIGNED & RESOURCE_RELEASED
            print("\n[TEST 4/6] Testing Resource Dispatch & Release -> WebSocket Broadcast...")
            assign_resp = client.post(
                f"/api/v1/incidents/{test_incident_id}/assign-resource",
                json={"resource_id": "RES-2004", "actor": "Test Dispatcher"}
            )
            assert assign_resp.status_code == 200, f"Assign failed: {assign_resp.text}"
            ws_assign = ws.receive_json()
            assert ws_assign.get("event") == "RESOURCE_ASSIGNED", f"Expected RESOURCE_ASSIGNED, got {ws_assign}"
            print(f"  ✓ WS Received: {ws_assign.get('event')} -> Resource RES-2004 assigned to {test_incident_id}")

            # Release resource
            release_resp = client.post(f"/api/v1/resources/RES-2004/release?actor=Test%20Commander")
            assert release_resp.status_code == 200, f"Release failed: {release_resp.text}"
            ws_release = ws.receive_json()
            assert ws_release.get("event") == "RESOURCE_RELEASED", f"Expected RESOURCE_RELEASED, got {ws_release}"
            print(f"  ✓ WS Received: {ws_release.get('event')} -> Resource RES-2004 released to AVAILABLE")

            # 5. TEST AI INCIDENT_CLASSIFIED BROADCAST
            print("\n[TEST 5/6] Testing AI Incident Analysis -> INCIDENT_CLASSIFIED Broadcast...")
            ai_resp = client.post(f"/api/v1/incidents/{test_incident_id}/analyze")
            assert ai_resp.status_code == 200, f"Analyze failed: {ai_resp.text}"
            ws_ai = ws.receive_json()
            assert ws_ai.get("event") == "INCIDENT_CLASSIFIED", f"Expected INCIDENT_CLASSIFIED, got {ws_ai}"
            print(f"  ✓ WS Received: {ws_ai.get('event')} for {ws_ai.get('data', {}).get('incident_id')}")

        # 6. TEST REST API STABILITY WITH ZERO WEBSOCKET CLIENTS
        print("\n[TEST 6/6] Verifying REST API Stability with 0 Connected WebSocket Clients...")
        assert ws_manager.client_count == 0, f"Expected 0 active clients, got {ws_manager.client_count}"

        # Perform REST operations without any active WS connection
        res_list = client.get("/api/v1/incidents/")
        assert res_list.status_code == 200, "REST listing failed with 0 WS clients"

        health = client.get("/api/v1/health")
        assert health.status_code == 200, "Health check failed"

        # Clean up test incident
        del_resp = client.delete(f"/api/v1/incidents/{test_incident_id}")
        assert del_resp.status_code == 200, "Delete incident failed"
        print(f"  ✓ REST API functions flawlessly with 0 WebSocket clients.")

    print("\n" + "=" * 75)
    print("✨ ALL 6 REAL-TIME WEBSOCKET VALIDATION TESTS PASSED 100%!")
    print("=" * 75)


if __name__ == "__main__":
    run_websocket_tests()
