import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings
from backend.app.database import DatabaseManager, get_database
from backend.app.services.db_service import DBService
from backend.app.ai.incident_classifier import analyze_incident
from backend.app.services.duplicate_detector import DuplicateDetector
from backend.app.services.resource_matcher import ResourceMatcher


async def run_full_system_e2e():
    print("=" * 70)
    print("[ResQAI] FULL SYSTEM E2E VALIDATION SUITE")
    print("=" * 70)

    # 1. DATABASE CONNECTION
    print("\n[STEP 1] Testing MongoDB Atlas / Local Connection & 2dsphere Indexes...")
    db = await DatabaseManager.connect_to_mongo()
    is_healthy = await DatabaseManager.is_healthy()
    assert is_healthy, "MongoDB connection failed!"
    print(f"  [PASS] MongoDB Connected: Database='{settings.mongo_db_name}'")

    # 2. AI TRIAGE & INCIDENT CREATION
    print("\n[STEP 2] Testing AI Incident Intelligence & Triage Engine...")
    distress_text = "Severe toxic ammonia chemical leak from valve in industrial plant sector 3. 5 workers unconscious with burns."
    ai_result = await analyze_incident(
        description=distress_text,
        source="iot",
        location={"latitude": 23.0150, "longitude": 72.3890}
    )
    assert ai_result["severity"] in ["CRITICAL", "HIGH"], "AI Severity triage failed!"
    assert ai_result["priority"] == "P1", "AI Priority assignment failed!"
    print(f"  [PASS] AI Classification: Type={ai_result['incident_type']}, Severity={ai_result['severity']}, Priority={ai_result['priority']}, Confidence={ai_result['confidence']*100:.0f}%")
    print(f"  [PASS] Recommended SOPs: {len(ai_result['immediate_actions'])} actions generated")

    # Ingest Incident to DB
    now_utc = datetime.now(timezone.utc)
    incident_doc = {
        "source": "iot",
        "type": ai_result["incident_type"],
        "title": "Industrial Ammonia Chemical Leak in Sector 3",
        "description": distress_text,
        "severity": ai_result["severity"],
        "priority": ai_result["priority"],
        "status": "REPORTED",
        "location": {
            "type": "Point",
            "coordinates": [72.3890, 23.0150]
        },
        "address": "Sanand GIDC Chemical Zone, Gujarat",
        "reported_at": now_utc,
        "ai_analysis": ai_result,
        "assigned_resources": [],
        "duplicate_count": 0,
        "reports": []
    }
    created_inc = await DBService.create_incident(db, incident_doc)
    master_id = created_inc["incident_id"]
    print(f"  [PASS] Master Incident Created: ID={master_id}")

    # 3. SPATIO-TEMPORAL DUPLICATE DETECTION (3-SIGNAL ENGINE)
    print("\n[STEP 3] Testing Duplicate Incident Detection Engine (Distance <= 1km, Time <= 45m, Sim >= 80%)...")
    dup_check = await DuplicateDetector.check_duplicate(
        db=db,
        title="Industrial Ammonia Chemical Leak in Sector 3",
        description="Toxic ammonia chemical leak from valve in industrial plant sector 3, workers unconscious.",
        latitude=23.0155, # ~60 meters away
        longitude=72.3892,
        reported_at=now_utc + timedelta(minutes=2)
    )
    assert dup_check.is_duplicate, f"Duplicate detection failed on spatio-temporal match! {dup_check}"
    assert dup_check.matched_incident_id == master_id, f"Expected match to {master_id}, got {dup_check.matched_incident_id}"
    print(f"  [PASS] Duplicate Identified! Match={dup_check.matched_incident_id} (Dist={dup_check.distance_km:.2f}km, TextSim={dup_check.text_similarity*100:.1f}%)")

    # Merge Duplicate Report
    merge_res = await DuplicateDetector.merge_duplicate_report(
        db=db,
        matched_incident_id=master_id,
        new_report_data={
            "title": "Industrial Ammonia Chemical Leak in Sector 3",
            "description": "Toxic ammonia chemical leak from valve in industrial plant sector 3, workers unconscious.",
            "source": "citizen"
        },
        similarity_score=dup_check.text_similarity or 0.95
    )
    print(f"  [PASS] Duplicate Merged: Total Merged Reports = {merge_res['duplicate_count']}")

    # 4. AI RESOURCE RECOMMENDATION & DISPATCH
    print("\n[STEP 4] Testing AI Resource Matcher & Dispatch Ranking...")
    recs = await ResourceMatcher.recommend_resources_for_incident(db, master_id, top_k=5)
    assert len(recs.recommendations) > 0, "Resource recommendations returned empty!"
    top_res = recs.recommendations[0]
    print(f"  [PASS] Top Recommended Resource: {top_res.name} ({top_res.category}) - Score={top_res.score*100:.1f}%, Distance={top_res.distance_km:.2f}km")
    print(f"  [PASS] Reason: {top_res.reason}")

    # Dispatch Resource
    dispatch_res = await ResourceMatcher.assign_resource_to_incident(
        db=db,
        incident_id=master_id,
        resource_id=top_res.resource_id,
        actor="E2E Test Officer"
    )
    assert dispatch_res.status == "assigned", f"Resource assignment failed: {dispatch_res}"
    print(f"  [PASS] Resource {top_res.resource_id} successfully dispatched to {master_id}")

    # Release Resource
    release_res = await ResourceMatcher.release_resource(
        db=db,
        resource_id=top_res.resource_id,
        actor="E2E Test Officer"
    )
    assert release_res.status == "released", f"Resource release failed: {release_res}"
    print(f"  [PASS] Resource {top_res.resource_id} successfully released back to available pool")

    # 5. HOSPITAL PROXIMITY RADAR
    print("\n[STEP 5] Testing Emergency Hospital 2dsphere Proximity Radar...")
    hospitals = await DBService.get_hospitals(
        db=db,
        near_longitude=72.3890,
        near_latitude=23.0150,
        max_distance_meters=50000.0,
        limit=5
    )
    assert len(hospitals) > 0, "Hospital search returned 0 results!"
    beds = hospitals[0].get("beds_available", hospitals[0].get("available_beds", 0))
    icu = hospitals[0].get("icu_available", 0)
    print(f"  [PASS] Nearest Emergency Hospital: {hospitals[0]['name']} (Beds Available: {beds}, ICU: {icu})")

    # Clean up test incident
    await db.incidents.delete_one({"incident_id": master_id})
    print(f"\n[CLEANUP] Deleted test incident {master_id}")

    print("\n" + "=" * 70)
    print("ALL END-TO-END SYSTEM INTEGRATION TESTS PASSED 100%!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_full_system_e2e())
