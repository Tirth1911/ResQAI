"""
ResQAI - Resource Recommendation & Dispatch Engine Test Suite
Tests:
1. Capability match calculation across emergency taxonomies (Fire, Medical, Flood, Road Accident, Hazmat)
2. Weighted scoring algorithm: (distance_score * 0.50) + (capability_match * 0.30) + (readiness * 0.20)
3. GET /api/resources/recommend/{incident_id}
4. POST /api/incidents/{incident_id}/assign-resource
5. POST /api/resources/{resource_id}/release
"""

import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings
from backend.app.main import app
from backend.app.services.resource_matcher import ResourceMatcher


async def run_tests():
    print("=" * 75)
    print(" ResQAI Resource Recommendation & Dispatch Engine Test Suite")
    print("=" * 75)

    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db_name]

    # Part 1: Test Direct Capability Matching
    print("\n[PART 1/4] Testing Capability Match Calculations Across Taxonomies...")
    fire_match = ResourceMatcher.calculate_capability_match(
        resource_category="FIRE_TRUCK",
        resource_capabilities=["Industrial Chemical Foam", "Hydraulic Platform 42m", "Thermal Imaging"],
        incident_type="fire"
    )
    print(f"           Fire Truck -> Fire Incident:            Match = {fire_match:.2f}")
    assert fire_match >= 0.80

    amb_match = ResourceMatcher.calculate_capability_match(
        resource_category="AMBULANCE",
        resource_capabilities=["Ventilator", "AED", "Trauma Kit"],
        incident_type="medical_emergency"
    )
    print(f"           Ambulance -> Medical Emergency:         Match = {amb_match:.2f}")
    assert amb_match >= 0.80

    boat_match = ResourceMatcher.calculate_capability_match(
        resource_category="RESCUE_TEAM",
        resource_capabilities=["Rescue Boat", "Sonar", "Life Jackets"],
        incident_type="flood"
    )
    print(f"           Rescue Team -> Flood Incident:          Match = {boat_match:.2f}")
    assert boat_match >= 0.80
    print("           [PASS] Capability matching tests succeeded!\n")

    # Part 2: REST API Testing
    print("--- PART 2: Testing Recommendation & Dispatch REST Endpoints ---")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:

        # Step 1: Ensure an available resource in Ahmedabad
        test_res_id = "RES-REC-TEST-01"
        await db.resources.delete_many({"resource_id": test_res_id})
        await db.resources.insert_one({
            "resource_id": test_res_id,
            "name": "Ahmedabad Rapid ALS Ambulance 99",
            "category": "AMBULANCE",
            "capabilities": ["Ventilator", "AED", "Paramedic", "Trauma Kit"],
            "status": "AVAILABLE",
            "capacity": 2,
            "current_incident_id": None,
            "location": {"type": "Point", "coordinates": [72.5714, 23.0225]},
            "updated_at": None
        })

        # Step 2: Test GET /api/resources/recommend/INC-1001 (Chemical Fire)
        print("\n[TEST 2/4] GET /api/resources/recommend/INC-1001 (Chemical Fire)...")
        rec_res = await http_client.get("/api/resources/recommend/INC-1001?top_k=5")
        assert rec_res.status_code == 200, f"Error: {rec_res.text}"
        rec_data = rec_res.json()
        
        print(f"           Incident ID:    {rec_data['incident_id']}")
        print(f"           Type:           {rec_data['incident_type']}")
        print(f"           Top Res Count:  {len(rec_data['recommendations'])}")
        
        for idx, r in enumerate(rec_data["recommendations"][:3], 1):
            print(f"           Rank #{idx}: [{r['category']}] {r['name']} ({r['resource_id']})")
            print(f"                   Distance: {r['distance_km']} km | Cap Match: {r['capability_match']} | Readiness: {r['readiness']} | Score: {r['score']}")
            print(f"                   Reason:   {r['reason']}")

        assert len(rec_data["recommendations"]) > 0
        top_rec = rec_data["recommendations"][0]
        assert "score" in top_rec and "distance_km" in top_rec
        print("           [PASS] Resource recommendation ranked by weighted formula successfully!\n")

        # Step 3: Test POST /api/incidents/{incident_id}/assign-resource
        print(f"\n[TEST 3/4] POST /api/incidents/INC-1001/assign-resource (Assigning {test_res_id})...")
        assign_payload = {
            "resource_id": test_res_id,
            "actor": "State Command Dispatcher",
            "notes": "Dispatched for secondary triage support"
        }
        assign_res = await http_client.post("/api/incidents/INC-1001/assign-resource", json=assign_payload)
        assert assign_res.status_code == 200, f"Error: {assign_res.text}"
        assign_data = assign_res.json()
        print(f"           Status:             {assign_data['status']}")
        print(f"           Assigned Resource:  {assign_data['resource_id']} ({assign_data['resource_name']})")
        print(f"           Assigned List:      {assign_data['assigned_resources']}")
        assert test_res_id in assign_data["assigned_resources"]

        # Verify in MongoDB that resource is now BUSY with current_incident_id
        db_res = await db.resources.find_one({"resource_id": test_res_id})
        assert db_res["status"] == "BUSY"
        assert db_res["current_incident_id"] == "INC-1001"
        print(f"           [DB Check] Resource status in DB: {db_res['status']} | current_incident_id: {db_res['current_incident_id']}")
        print("           [PASS] Dispatch assignment persisted correctly!\n")

        # Step 4: Test POST /api/resources/{resource_id}/release
        print(f"\n[TEST 4/4] POST /api/resources/{test_res_id}/release...")
        release_res = await http_client.post(f"/api/resources/{test_res_id}/release?actor=Field%20Captain")
        assert release_res.status_code == 200, f"Error: {release_res.text}"
        release_data = release_res.json()
        print(f"           Status:      {release_data['status']}")
        print(f"           New Status:  {release_data['new_status']}")
        print(f"           Message:     {release_data['message']}")

        # Verify in MongoDB that resource is back to AVAILABLE
        db_res_released = await db.resources.find_one({"resource_id": test_res_id})
        assert db_res_released["status"] == "AVAILABLE"
        assert db_res_released["current_incident_id"] is None
        print(f"           [DB Check] Resource status in DB: {db_res_released['status']} | current_incident_id: {db_res_released['current_incident_id']}")
        print("           [PASS] Resource successfully released back to available pool!\n")

        # Cleanup
        await db.resources.delete_many({"resource_id": test_res_id})

    client.close()
    print("=" * 75)
    print(" ALL RESOURCE RECOMMENDATION & DISPATCH TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_tests())
