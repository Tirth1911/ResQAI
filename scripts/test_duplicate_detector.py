"""
ResQAI - Duplicate Incident Detection Engine Test Suite
Tests 5 critical validation cases:
1. Exact duplicate (Same coords, within 45 mins, identical text) -> DUPLICATE: TRUE
2. Nearby duplicate (0.3 km away, within 45 mins, high text similarity) -> DUPLICATE: TRUE
3. Same text but far away (50 km away in Vadodara) -> DUPLICATE: FALSE
4. Same location but different time (90 minutes later) -> DUPLICATE: FALSE
5. Unrelated incident (Same location, completely different emergency) -> DUPLICATE: FALSE

Also tests:
- POST /api/incidents/check-duplicate endpoint
- GET /api/incidents/{incident_id}/related endpoint
- Explainability output
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings
from backend.app.main import app
from backend.app.services.duplicate_detector import DuplicateDetector

AHMEDABAD_LAT = 23.0225
AHMEDABAD_LON = 72.5714

VADODARA_LAT = 22.3072
VADODARA_LON = 73.1812


async def run_tests():
    print("=" * 75)
    print(" ResQAI Duplicate Incident Detection Engine - 5-Case Test Suite")
    print("=" * 75)

    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db_name]

    now_utc = datetime.now(timezone.utc)

    # Clean up any leftover test records
    await db.incidents.delete_many({"incident_id": {"$regex": "^INC-DEDUP-"}})

    # Setup Master Incident in MongoDB
    master_incident = {
        "incident_id": "INC-DEDUP-MASTER",
        "title": "Major Industrial Chemical Fire in GIDC Warehouse",
        "description": "Explosion in solvent distillation plant block 4. Heavy black smoke and visible flames near gate 2. Multiple casualties trapped.",
        "source": "call_center",
        "type": "fire",
        "severity": "CRITICAL",
        "priority": "P1",
        "status": "DISPATCHED",
        "location": {"type": "Point", "coordinates": [AHMEDABAD_LON, AHMEDABAD_LAT]},
        "address": "GIDC Vatva Industrial Zone, Ahmedabad",
        "reported_at": now_utc - timedelta(minutes=10),
        "updated_at": now_utc - timedelta(minutes=10),
        "duplicate_count": 0,
        "reports": [],
        "timeline": [{"timestamp": now_utc - timedelta(minutes=10), "action": "Incident Reported", "actor": "call_center"}]
    }
    await db.incidents.insert_one(master_incident)
    print(f"\n[SETUP] Seeded Master Incident '{master_incident['incident_id']}' at ({AHMEDABAD_LAT}, {AHMEDABAD_LON}) - Reported 10 mins ago.\n")

    try:
        # ---------------------------------------------------------------------
        # TEST CASE 1: Exact Duplicate
        # ---------------------------------------------------------------------
        print("[TEST 1/5] Exact Duplicate (Same location, reported now, identical description)...")
        res1 = await DuplicateDetector.check_duplicate(
            db=db,
            title="Major Industrial Chemical Fire in GIDC Warehouse",
            description="Explosion in solvent distillation plant block 4. Heavy black smoke and visible flames near gate 2. Multiple casualties trapped.",
            latitude=AHMEDABAD_LAT,
            longitude=AHMEDABAD_LON,
            reported_at=now_utc
        )
        print(f"           Is Duplicate:    {res1.is_duplicate}")
        print(f"           Matched ID:      {res1.matched_incident_id}")
        print(f"           Distance:        {res1.distance_km} km")
        print(f"           Time Diff:       {res1.time_diff_minutes} mins")
        print(f"           Text Similarity: {res1.text_similarity}")
        print(f"           Explanation:     {res1.explanation}")
        assert res1.is_duplicate is True, "Test 1 Failed: Should be classified as DUPLICATE"
        assert res1.matched_incident_id == "INC-DEDUP-MASTER"
        print("           [PASS] Test 1 Succeeded!\n")

        # ---------------------------------------------------------------------
        # TEST CASE 2: Nearby Duplicate
        # ---------------------------------------------------------------------
        print("[TEST 2/5] Nearby Duplicate (0.3 km away, within 45 mins, phrased report)...")
        nearby_lat = AHMEDABAD_LAT + 0.0025
        nearby_lon = AHMEDABAD_LON + 0.0020
        res2 = await DuplicateDetector.check_duplicate(
            db=db,
            title="Major Industrial Chemical Fire in GIDC Warehouse",
            description="Explosion in solvent distillation plant block 4. Heavy black smoke and visible flames near gate 2. Multiple casualties trapped inside.",
            latitude=nearby_lat,
            longitude=nearby_lon,
            reported_at=now_utc - timedelta(minutes=5)
        )
        print(f"           Is Duplicate:    {res2.is_duplicate}")
        print(f"           Matched ID:      {res2.matched_incident_id}")
        print(f"           Distance:        {res2.distance_km} km (<= 1.0 km threshold)")
        print(f"           Time Diff:       {res2.time_diff_minutes} mins (<= 45 mins threshold)")
        print(f"           Text Similarity: {res2.text_similarity} (>= 0.80 threshold)")
        print(f"           Explanation:     {res2.explanation}")
        assert res2.is_duplicate is True, "Test 2 Failed: Nearby duplicate should be detected"
        assert res2.distance_km <= 1.0
        assert res2.text_similarity >= 0.80
        print("           [PASS] Test 2 Succeeded!\n")

        # ---------------------------------------------------------------------
        # TEST CASE 3: Same Text But Far Away (50+ km away in Vadodara)
        # ---------------------------------------------------------------------
        print("[TEST 3/5] Same Text But Far Away (50+ km away in Vadodara)...")
        res3 = await DuplicateDetector.check_duplicate(
            db=db,
            title="Major Industrial Chemical Fire in GIDC Warehouse",
            description="Explosion in solvent distillation plant block 4. Heavy black smoke and visible flames near gate 2.",
            latitude=VADODARA_LAT,
            longitude=VADODARA_LON,
            reported_at=now_utc
        )
        print(f"           Is Duplicate:    {res3.is_duplicate}")
        print(f"           Matched ID:      {res3.matched_incident_id}")
        print(f"           Explanation:     {res3.explanation}")
        assert res3.is_duplicate is False, "Test 3 Failed: Far away report should NOT be a duplicate"
        print("           [PASS] Test 3 Succeeded!\n")

        # ---------------------------------------------------------------------
        # TEST CASE 4: Same Location But Different Time (90 mins later)
        # ---------------------------------------------------------------------
        print("[TEST 4/5] Same Location But Different Time (90 minutes later)...")
        res4 = await DuplicateDetector.check_duplicate(
            db=db,
            title="Major Industrial Chemical Fire in GIDC Warehouse",
            description="Explosion in solvent distillation plant block 4. Heavy black smoke and visible flames near gate 2.",
            latitude=AHMEDABAD_LAT,
            longitude=AHMEDABAD_LON,
            reported_at=now_utc + timedelta(minutes=90)
        )
        print(f"           Is Duplicate:    {res4.is_duplicate}")
        print(f"           Matched ID:      {res4.matched_incident_id}")
        print(f"           Explanation:     {res4.explanation}")
        assert res4.is_duplicate is False, "Test 4 Failed: Outside temporal window should NOT be duplicate"
        print("           [PASS] Test 4 Succeeded!\n")

        # ---------------------------------------------------------------------
        # TEST CASE 5: Unrelated Incident (Same area, completely different issue)
        # ---------------------------------------------------------------------
        print("[TEST 5/5] Unrelated Incident (Same area, cardiac medical emergency vs chemical fire)...")
        res5 = await DuplicateDetector.check_duplicate(
            db=db,
            title="Passenger collapsed with acute cardiac arrest at bus stop",
            description="50-year-old male unconscious without pulse. CPR ongoing. Ambulance required immediately.",
            latitude=AHMEDABAD_LAT,
            longitude=AHMEDABAD_LON,
            reported_at=now_utc
        )
        print(f"           Is Duplicate:    {res5.is_duplicate}")
        print(f"           Matched ID:      {res5.matched_incident_id}")
        print(f"           Explanation:     {res5.explanation}")
        assert res5.is_duplicate is False, "Test 5 Failed: Unrelated emergency should NOT be a duplicate"
        print("           [PASS] Test 5 Succeeded!\n")

        # ---------------------------------------------------------------------
        # PART 2: REST API ENDPOINTS TEST (check-duplicate & related)
        # ---------------------------------------------------------------------
        print("--- PART 2: Testing REST API Endpoints ---")
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
            
            # API Test 1: POST /api/incidents/check-duplicate
            print("\n[API 1/3] POST /api/incidents/check-duplicate...")
            check_payload = {
                "title": "Major Industrial Chemical Fire in GIDC Warehouse",
                "description": "Explosion in solvent distillation plant block 4. Heavy black smoke and visible flames near gate 2.",
                "location": {"latitude": AHMEDABAD_LAT + 0.001, "longitude": AHMEDABAD_LON + 0.001},
                "source": "citizen"
            }
            api_res = await http_client.post("/api/incidents/check-duplicate", json=check_payload)
            assert api_res.status_code == 200
            check_data = api_res.json()
            print(f"          API Response: is_duplicate={check_data['is_duplicate']}, matched_id={check_data['matched_incident_id']}, similarity={check_data.get('text_similarity')}")
            assert check_data["is_duplicate"] is True
            assert check_data["matched_incident_id"] == "INC-DEDUP-MASTER"

            # API Test 2: Auto-merge via POST /api/incidents/?auto_dedup=true
            print("\n[API 2/3] POST /api/incidents/?auto_dedup=true (Testing live duplicate merge)...")
            ingest_payload = {
                "title": "Citizen Call: Major Industrial Chemical Fire in GIDC Warehouse",
                "description": "Explosion in solvent distillation plant block 4. Heavy black smoke and visible flames near gate 2.",
                "source": "citizen",
                "location": {
                    "latitude": AHMEDABAD_LAT + 0.001,
                    "longitude": AHMEDABAD_LON + 0.001,
                    "address": "Near Gate 2, Vatva GIDC"
                }
            }
            ingest_res = await http_client.post("/api/incidents/?auto_dedup=true", json=ingest_payload)
            assert ingest_res.status_code == 201
            merged_doc = ingest_res.json()
            assert merged_doc["incident_id"] == "INC-DEDUP-MASTER", "Duplicate report should merge into master incident"
            print(f"          Master Incident '{merged_doc['incident_id']}' duplicate count updated to: {merged_doc.get('duplicate_count', 1)}")

            # API Test 3: GET /api/incidents/{incident_id}/related
            print("\n[API 3/3] GET /api/incidents/INC-DEDUP-MASTER/related...")
            related_res = await http_client.get("/api/incidents/INC-DEDUP-MASTER/related")
            assert related_res.status_code == 200
            related_data = related_res.json()
            print(f"          Incident ID:        {related_data['incident_id']}")
            print(f"          Merged Reports:     {len(related_data['reports'])}")
            print(f"          Timeline Events:    {len(related_data['timeline'])}")
            print(f"          Nearby Incidents:   {len(related_data['nearby_active_incidents'])}")
            assert len(related_data["reports"]) >= 1

    finally:
        # Cleanup
        await db.incidents.delete_many({"incident_id": {"$regex": "^INC-DEDUP-"}})
        client.close()

    print("\n" + "=" * 75)
    print(" ALL 5 DUPLICATE DETECTION CASES AND API ENDPOINTS PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_tests())
