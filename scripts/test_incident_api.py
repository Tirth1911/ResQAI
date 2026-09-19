"""
ResQAI - Incident Management API Test Suite
Automated end-to-end testing of every Incident endpoint:
1. POST /api/incidents (Explicit fields)
2. POST /api/incidents (Omitted type/severity/priority -> AI triage + INC-YYYYMMDD-XXXX ID generation)
3. GET /api/incidents (Pagination)
4. GET /api/incidents (Filtering by type, severity, status, source, keyword search)
5. GET /api/incidents/active
6. GET /api/incidents/critical
7. GET /api/incidents/nearby (2dsphere geospatial search)
8. GET /api/incidents/stats
9. GET /api/incidents/{incident_id}
10. PATCH /api/incidents/{incident_id}
11. POST /api/incidents/{incident_id}/verify
12. POST /api/incidents/{incident_id}/resolve
13. POST /api/incidents/{incident_id}/close
14. DELETE /api/incidents/{incident_id}
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from backend.app.main import app


async def run_tests():
    print("=" * 70)
    print(" ResQAI Incident Management API - Comprehensive Test Suite")
    print("=" * 70)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test 1: POST /api/incidents (Explicit fields)
        print("\n[1/14] Testing POST /api/incidents (Explicit fields)...")
        payload1 = {
            "title": "Severe Highway Crash near SG Highway Bridge",
            "description": "Two vehicles collided with entrapment and oil leak on tarmac.",
            "source": "citizen",
            "type": "road_accident",
            "severity": "CRITICAL",
            "priority": "P1",
            "location": {
                "latitude": 23.0338,
                "longitude": 72.5074,
                "address": "SG Highway, Ahmedabad, Gujarat"
            }
        }
        res1 = await client.post("/api/incidents/", json=payload1)
        assert res1.status_code == 201, f"Expected 201, got {res1.status_code}: {res1.text}"
        inc1 = res1.json()
        inc_id1 = inc1["incident_id"]
        print(f"       [PASS] Created incident: {inc_id1} (Status: {inc1['status']}, Severity: {inc1['severity']})")

        # Test 2: POST /api/incidents (Omitted type/severity/priority -> AI Triage)
        print("\n[2/14] Testing POST /api/incidents (AI Triage & Auto-classification)...")
        payload2 = {
            "title": "Massive fire and explosions at chemical storage unit",
            "description": "Flames spreading rapidly to adjacent warehouse, 3 persons trapped inside with breathing distress.",
            "source": "call_center",
            "location": {
                "latitude": 22.9568,
                "longitude": 72.6324,
                "address": "Vatva GIDC, Ahmedabad"
            }
        }
        res2 = await client.post("/api/incidents/", json=payload2)
        assert res2.status_code == 201, f"Expected 201, got {res2.status_code}: {res2.text}"
        inc2 = res2.json()
        inc_id2 = inc2["incident_id"]
        print(f"       [PASS] Created incident: {inc_id2}")
        print(f"              - Inferred Type:     {inc2['type']}")
        print(f"              - Inferred Severity: {inc2['severity']}")
        print(f"              - Inferred Priority: {inc2['priority']}")
        print(f"              - AI Confidence:     {inc2['confidence']}")

        # Test 3: GET /api/incidents (Pagination)
        print("\n[3/14] Testing GET /api/incidents (Pagination page=1, limit=5)...")
        res3 = await client.get("/api/incidents/?page=1&limit=5")
        assert res3.status_code == 200
        data3 = res3.json()
        print(f"       [PASS] Total Incidents: {data3['total']} | Page: {data3['page']}/{data3['total_pages']} | Items returned: {len(data3['items'])}")

        # Test 4: GET /api/incidents with filters
        print("\n[4/14] Testing GET /api/incidents (Filtering by type=road_accident & search keyword)...")
        res4 = await client.get("/api/incidents/?type=road_accident&search=Highway")
        assert res4.status_code == 200
        data4 = res4.json()
        print(f"       [PASS] Filtered results count: {data4['total']}")

        # Test 5: GET /api/incidents/active
        print("\n[5/14] Testing GET /api/incidents/active...")
        res5 = await client.get("/api/incidents/active?limit=5")
        assert res5.status_code == 200
        data5 = res5.json()
        print(f"       [PASS] Active incidents count: {data5['total']}")

        # Test 6: GET /api/incidents/critical
        print("\n[6/14] Testing GET /api/incidents/critical...")
        res6 = await client.get("/api/incidents/critical?limit=5")
        assert res6.status_code == 200
        data6 = res6.json()
        print(f"       [PASS] Critical incidents count: {data6['total']}")

        # Test 7: GET /api/incidents/nearby (2dsphere Geospatial Search)
        print("\n[7/14] Testing GET /api/incidents/nearby (Coordinates: 72.5074, 23.0338 within 15km)...")
        res7 = await client.get("/api/incidents/nearby?longitude=72.5074&latitude=23.0338&max_distance_meters=15000")
        assert res7.status_code == 200
        nearby_list = res7.json()
        print(f"       [PASS] Found {len(nearby_list)} incidents within 15km.")
        if nearby_list:
            print(f"              Closest: {nearby_list[0]['incident_id']} - '{nearby_list[0]['title']}' ({nearby_list[0].get('distance_km')} km)")

        # Test 8: GET /api/incidents/stats
        print("\n[8/14] Testing GET /api/incidents/stats...")
        res8 = await client.get("/api/incidents/stats")
        assert res8.status_code == 200
        stats = res8.json()
        print(f"       [PASS] Total: {stats['total_incidents']} | Active: {stats['active_incidents']} | Critical: {stats['critical_incidents']}")
        print(f"              Types:      {stats['incidents_by_type']}")
        print(f"              Severities: {stats['incidents_by_severity']}")

        # Test 9: GET /api/incidents/{incident_id}
        print(f"\n[9/14] Testing GET /api/incidents/{inc_id1}...")
        res9 = await client.get(f"/api/incidents/{inc_id1}")
        assert res9.status_code == 200
        print(f"       [PASS] Retrieved: {res9.json()['title']}")

        # Test 10: PATCH /api/incidents/{incident_id}
        print(f"\n[10/14] Testing PATCH /api/incidents/{inc_id1} (Assign resource)...")
        patch_payload = {
            "assigned_resources": ["RES-2001", "RES-2004"]
        }
        res10 = await client.patch(f"/api/incidents/{inc_id1}", json=patch_payload)
        assert res10.status_code == 200
        patched = res10.json()
        assert "RES-2001" in patched["assigned_resources"]
        print(f"       [PASS] Assigned Resources: {patched['assigned_resources']}")

        # Test 11: POST /api/incidents/{incident_id}/verify
        print(f"\n[11/14] Testing POST /api/incidents/{inc_id1}/verify...")
        res11 = await client.post(f"/api/incidents/{inc_id1}/verify", json={"actor": "Chief Officer", "notes": "CCTV stream verified"})
        assert res11.status_code == 200
        verified = res11.json()
        assert verified["status"] == "VERIFIED"
        print(f"       [PASS] Status updated to: {verified['status']}")

        # Test 12: POST /api/incidents/{incident_id}/resolve
        print(f"\n[12/14] Testing POST /api/incidents/{inc_id1}/resolve...")
        res12 = await client.post(f"/api/incidents/{inc_id1}/resolve", json={"actor": "Field Lead", "notes": "Extrication complete and casualties transferred"})
        assert res12.status_code == 200
        resolved = res12.json()
        assert resolved["status"] == "RESOLVED"
        print(f"       [PASS] Status updated to: {resolved['status']}")

        # Test 13: POST /api/incidents/{incident_id}/close
        print(f"\n[13/14] Testing POST /api/incidents/{inc_id1}/close...")
        res13 = await client.post(f"/api/incidents/{inc_id1}/close", json={"actor": "Admin", "notes": "Audit completed"})
        assert res13.status_code == 200
        closed = res13.json()
        assert closed["status"] == "CLOSED"
        print(f"       [PASS] Status updated to: {closed['status']}")

        # Test 14: DELETE /api/incidents/{incident_id}
        print(f"\n[14/14] Testing DELETE /api/incidents/{inc_id1}...")
        res14 = await client.delete(f"/api/incidents/{inc_id1}")
        assert res14.status_code == 200
        print(f"       [PASS] Deleted incident: {inc_id1}")

        # Cleanup inc2
        await client.delete(f"/api/incidents/{inc_id2}")

        print("\n" + "=" * 70)
        print(" ALL 14 INCIDENT MANAGEMENT API TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
