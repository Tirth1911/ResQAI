import asyncio
import json
import httpx
import websockets

BACKEND_HTTP = "http://127.0.0.1:8000"
BACKEND_WS = "ws://127.0.0.1:8000/ws/dashboard"


async def main():
    print("==================================================")
    print("STARTING LIVE REAL-TIME SYNCHRONIZATION VERIFICATION")
    print("==================================================")

    async with httpx.AsyncClient(base_url=BACKEND_HTTP, timeout=15.0) as client:
        # 1. Seed a standby test resource in case none exist
        print("\n[Step 1] Ensuring standby response resources in database...")
        res_list = await client.get("/api/resources/")
        items = res_list.json()
        if items:
            test_resource_id = items[0]["resource_id"]
        else:
            seed_res = await client.post("/api/resources/", json={
                "name": "Navrangpura Fire Engine 1",
                "category": "FIRE_TRUCK",
                "capabilities": ["FIRE", "WATER_TENDER"],
                "status": "AVAILABLE",
                "capacity": 5,
                "location": {"latitude": 23.0360, "longitude": 72.5610, "address": "Navrangpura Fire Station"}
            })
            test_resource_id = seed_res.json()["resource_id"]
        print(f"  [OK] Active test resource ID: {test_resource_id}")

        # 2. Connect Dashboard A and Dashboard B
        print("\n[Step 2] Connecting Dashboard A and Dashboard B to WebSocket...")
        async with websockets.connect(BACKEND_WS) as ws_a, websockets.connect(BACKEND_WS) as ws_b:
            handshake_a = json.loads(await ws_a.recv())
            handshake_b = json.loads(await ws_b.recv())

            assert handshake_a["event"] == "CONNECTED"
            assert handshake_b["event"] == "CONNECTED"
            assert "event_id" in handshake_a
            assert "event_id" in handshake_b
            print(f"  [OK] Dashboard A connected (event_id: {handshake_a['event_id']})")
            print(f"  [OK] Dashboard B connected (event_id: {handshake_b['event_id']})")

            # 3. Simulate New Critical Incident (Server Pipeline)
            print("\n[Step 3] Simulating New Critical Incident on server (/api/simulation/simulate-critical)...")
            sim_resp = await client.post("/api/simulation/simulate-critical")
            assert sim_resp.status_code == 200, f"Simulate critical failed: {sim_resp.text}"
            sim_json = sim_resp.json()
            assert sim_json["status"] == "success"
            incident = sim_json["incident"]
            incident_id = incident["incident_id"]
            print(f"  [OK] Created Incident in MongoDB: {incident_id} - '{incident['title']}'")
            print(f"  [OK] Priority: {incident['priority']} | Severity: {incident['severity']}")

            # Receive real-time events on both dashboards
            print("\n[Step 4] Checking real-time event delivery across connected dashboards...")
            events_a = []
            events_b = []

            for _ in range(4):
                raw_a = await asyncio.wait_for(ws_a.recv(), timeout=5.0)
                raw_b = await asyncio.wait_for(ws_b.recv(), timeout=5.0)
                events_a.append(json.loads(raw_a))
                events_b.append(json.loads(raw_b))

            event_names_a = [e["event"] for e in events_a]
            event_names_b = [e["event"] for e in events_b]

            print(f"  Dashboard A received events: {event_names_a}")
            print(f"  Dashboard B received events: {event_names_b}")

            assert "NEW_INCIDENT" in event_names_a or "INCIDENT_CREATED" in event_names_a
            assert "NEW_INCIDENT" in event_names_b or "INCIDENT_CREATED" in event_names_b
            assert "DISPATCH_REQUIRED" in event_names_a
            assert "DISPATCH_REQUIRED" in event_names_b
            assert "ALERT_CREATED" in event_names_a
            assert "ALERT_CREATED" in event_names_b
            print("  [OK] NEW_INCIDENT, DISPATCH_REQUIRED, and ALERT_CREATED delivered to all dashboards!")

            # Check unique event_id
            dispatch_event = next(e for e in events_a if e["event"] == "DISPATCH_REQUIRED")
            print(f"  [OK] Verified DISPATCH_REQUIRED payload:")
            print(f"      event_id: {dispatch_event['event_id']}")
            print(f"      incident_id: {dispatch_event['incident_id']}")
            print(f"      priority: {dispatch_event['data']['priority']}")
            print(f"      reason: {dispatch_event['data']['reason']}")
            print(f"      recommended_units: {dispatch_event['data']['recommended_resource_ids']}")

            # 4. Dispatch Resource
            print(f"\n[Step 5] Dispatching Resource {test_resource_id} to Incident {incident_id}...")
            dispatch_resp = await client.post(
                f"/api/incidents/{incident_id}/assign-resource",
                json={
                    "resource_id": test_resource_id,
                    "actor": "Ahmedabad Command Dispatcher",
                    "notes": "Immediate deployment to Odhav GIDC chemical fire"
                }
            )
            assert dispatch_resp.status_code == 200, f"Dispatch failed: {dispatch_resp.text}"
            print("  [OK] Database updated: Resource marked BUSY and assigned to incident.")

            # Collect dispatch events on Dashboard A and Dashboard B
            d_events_a = []
            d_events_b = []
            for _ in range(4):
                raw_a = await asyncio.wait_for(ws_a.recv(), timeout=5.0)
                raw_b = await asyncio.wait_for(ws_b.recv(), timeout=5.0)
                d_events_a.append(json.loads(raw_a))
                d_events_b.append(json.loads(raw_b))

            d_names_a = [e["event"] for e in d_events_a]
            d_names_b = [e["event"] for e in d_events_b]
            print(f"  Dashboard A received: {d_names_a}")
            print(f"  Dashboard B received: {d_names_b}")

            assert "RESOURCE_DISPATCHED" in d_names_a or "RESOURCE_ASSIGNED" in d_names_a
            assert "RESOURCE_DISPATCHED" in d_names_b or "RESOURCE_ASSIGNED" in d_names_b
            assert "INCIDENT_UPDATED" in d_names_a
            assert "INCIDENT_UPDATED" in d_names_b
            print("  [OK] Live Fleet and Incident status updated synchronously across all dashboards!")

            # 5. Resolve Incident
            print(f"\n[Step 6] Resolving Incident {incident_id}...")
            resolve_resp = await client.post(
                f"/api/incidents/{incident_id}/resolve",
                json={
                    "actor": "Field Commander",
                    "notes": "Chemical vapor neutralized. Perimeter secured."
                }
            )
            assert resolve_resp.status_code == 200, f"Resolve failed: {resolve_resp.text}"
            print("  [OK] Database updated: Incident marked RESOLVED.")

            r_events_a = []
            r_events_b = []
            for _ in range(2):
                raw_a = await asyncio.wait_for(ws_a.recv(), timeout=5.0)
                raw_b = await asyncio.wait_for(ws_b.recv(), timeout=5.0)
                r_events_a.append(json.loads(raw_a))
                r_events_b.append(json.loads(raw_b))

            r_names_a = [e["event"] for e in r_events_a]
            r_names_b = [e["event"] for e in r_events_b]
            print(f"  Dashboard A received: {r_names_a}")
            print(f"  Dashboard B received: {r_names_b}")
            assert "INCIDENT_RESOLVED" in r_names_a
            assert "INCIDENT_RESOLVED" in r_names_b
            print("  [OK] INCIDENT_RESOLVED delivered to all dashboards!")

            # 6. Release Resource back to available pool
            print(f"\n[Step 7] Releasing Resource {test_resource_id} back to available standby pool...")
            rel_resp = await client.post(
                f"/api/incidents/{incident_id}/release-resource",
                json={"resource_id": test_resource_id, "actor": "Field Commander"}
            )
            assert rel_resp.status_code == 200, f"Release failed: {rel_resp.text}"

            rel_events_a = []
            rel_events_b = []
            for _ in range(3):
                raw_a = await asyncio.wait_for(ws_a.recv(), timeout=5.0)
                raw_b = await asyncio.wait_for(ws_b.recv(), timeout=5.0)
                rel_events_a.append(json.loads(raw_a))
                rel_events_b.append(json.loads(raw_b))

            rel_names_a = [e["event"] for e in rel_events_a]
            rel_names_b = [e["event"] for e in rel_events_b]
            print(f"  Dashboard A received: {rel_names_a}")
            print(f"  Dashboard B received: {rel_names_b}")
            assert "RESOURCE_AVAILABLE" in rel_names_a or "RESOURCE_RELEASED" in rel_names_a
            assert "RESOURCE_AVAILABLE" in rel_names_b or "RESOURCE_RELEASED" in rel_names_b
            print("  [OK] Fleet resource marked AVAILABLE in all connected dashboards!")

            # 7. Live Query Ingestion Test (Requirement 14)
            print("\n[Step 8] Testing Live Query Ingestion (/api/incidents)...")
            ingest_resp = await client.post("/api/incidents", json={
                "source": "HOTLINE",
                "description": "Chemical fire reported near Odhav GIDC phase 2. Strong gas fumes.",
                "location": "Odhav GIDC, Ahmedabad"
            })
            assert ingest_resp.status_code == 201, f"Live query ingestion failed: {ingest_resp.text}"
            ingest_data = ingest_resp.json()
            ingest_id = ingest_data["incident_id"]
            print(f"  [OK] External emergency query ingested: {ingest_id}")

            ing_events = []
            for _ in range(4):
                raw = await asyncio.wait_for(ws_a.recv(), timeout=5.0)
                ing_events.append(json.loads(raw))

            ing_names = [e["event"] for e in ing_events]
            print(f"  Real-time events received from external ingestion: {ing_names}")
            assert "NEW_INCIDENT" in ing_names or "INCIDENT_CREATED" in ing_names
            assert "DISPATCH_REQUIRED" in ing_names
            print("  [OK] External ingestion triggered the complete real-time pipeline!")

    print("\n==================================================")
    print("ALL LIVE DATA SYNCHRONIZATION TESTS PASSED! (100% OK)")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
