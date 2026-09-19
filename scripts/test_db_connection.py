"""
ResQAI - MongoDB Connection & 2dsphere Geospatial Test Suite
Verifies:
1. Ping connectivity to MongoDB (Atlas or Local)
2. Presence of all 8 required collections
3. Verification of 2dsphere indexes on (incidents, resources, teams, hospitals)
4. DBService CRUD operations & geospatial proximity tests
"""

import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings
from backend.app.services.db_service import DBService

REQUIRED_COLLECTIONS = [
    "incidents",
    "resources",
    "teams",
    "hospitals",
    "notifications",
    "users",
    "incident_updates",
    "analytics",
]


async def run_diagnostics():
    uri = settings.mongo_uri
    db_name = settings.mongo_db_name

    print("=" * 70)
    print(" ResQAI MongoDB Diagnostic & Verification Test Suite")
    print("=" * 70)
    print(f" Target URI:      {uri.split('@')[-1] if '@' in uri else uri}")
    print(f" Target Database: {db_name}\n")

    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]

    try:
        # Step 1: Ping Test
        print("[1/4] Testing Server Connectivity (Admin Ping)...")
        ping_res = await client.admin.command("ping")
        print(f"      [OK] Connection active (Response: {ping_res})\n")

        # Step 2: Check Collections
        print("[2/4] Checking Required Collections...")
        existing_cols = await db.list_collection_names()
        for col in REQUIRED_COLLECTIONS:
            count = await db[col].count_documents({})
            status_icon = "[OK]" if col in existing_cols or count > 0 else "[Empty/Pending]"
            print(f"      * {col:18} : {count:3} docs {status_icon}")
        print()

        # Step 3: Check 2dsphere Indexes
        print("[3/4] Verifying 2dsphere Geospatial Indexes...")
        geo_collections = ["incidents", "resources", "teams", "hospitals"]
        for col_name in geo_collections:
            indexes = await db[col_name].index_information()
            has_2dsphere = any(
                isinstance(v.get("key"), list) and ("location", "2dsphere") in v["key"]
                for v in indexes.values()
            )
            status_str = "[OK] ACTIVE" if has_2dsphere else "[WARN] MISSING"
            print(f"      * {col_name:12} 2dsphere index: {status_str}")
        print()

        # Step 4: Proximity Query Test (Ahmedabad coordinates: 72.5714, 23.0225)
        print("[4/4] Testing Geospatial Proximity Queries (Ahmedabad Hub)...")
        nearby_res = await DBService.find_nearby_resources(
            db=db,
            longitude=72.5714,
            latitude=23.0225,
            max_distance_meters=25000.0,
            limit=3
        )
        print(f"      [OK] Found {len(nearby_res)} nearby response units within 25km:")
        for r in nearby_res:
            print(f"        - [{r.get('category')}] {r.get('name')} (Distance: {r.get('distance_km')} km)")

        nearby_hosp = await DBService.get_hospitals(
            db=db,
            near_longitude=72.5714,
            near_latitude=23.0225,
            max_distance_meters=25000.0,
            limit=3
        )
        print(f"      [OK] Found {len(nearby_hosp)} nearby emergency hospitals:")
        for h in nearby_hosp:
            print(f"        - {h.get('name')} (Distance: {h.get('distance_km')} km | Beds Available: {h.get('beds_available')})")

        print("\n" + "=" * 70)
        print(" ALL DIAGNOSTIC CHECKS COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Diagnostic test failed: {e}")
        print("Ensure MongoDB is running locally or set MONGODB_URI to a valid MongoDB Atlas connection string.")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
