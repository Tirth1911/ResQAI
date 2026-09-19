"""
Seed script to initialize MongoDB with default emergency response units.
Usage:
    python scripts/seed_data.py
"""
import asyncio
import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "resqai")

SAMPLE_RESOURCES = [
    {
        "call_sign": "AMB-ALPHA-101",
        "type": "Ambulance",
        "status": "AVAILABLE",
        "capacity": 2,
        "contact_phone": "+91-9876543210",
        "station_name": "City General Hospital",
        "assigned_incident_id": None,
        "location": {"type": "Point", "coordinates": [77.5946, 12.9716]},
        "address": "Koramangala, Bangalore",
        "last_updated": datetime.utcnow(),
    },
    {
        "call_sign": "FIRE-BRAVO-01",
        "type": "Fire Truck",
        "status": "AVAILABLE",
        "capacity": 6,
        "contact_phone": "+91-9876543211",
        "station_name": "Central Fire Station #4",
        "assigned_incident_id": None,
        "location": {"type": "Point", "coordinates": [77.6012, 12.9650]},
        "address": "MG Road, Bangalore",
        "last_updated": datetime.utcnow(),
    },
    {
        "call_sign": "POLICE-CHARLIE-07",
        "type": "Police Patrol",
        "status": "AVAILABLE",
        "capacity": 4,
        "contact_phone": "+91-9876543212",
        "station_name": "South Division HQ",
        "assigned_incident_id": None,
        "location": {"type": "Point", "coordinates": [77.6245, 12.9352]},
        "address": "Outer Ring Road, Bangalore",
        "last_updated": datetime.utcnow(),
    },
    {
        "call_sign": "RESCUE-BOAT-DELTA-02",
        "type": "Rescue Boat",
        "status": "AVAILABLE",
        "capacity": 8,
        "contact_phone": "+91-9876543213",
        "station_name": "Disaster Quick Response Unit",
        "assigned_incident_id": None,
        "location": {"type": "Point", "coordinates": [77.6101, 12.9165]},
        "address": "BTM Lake Base, Bangalore",
        "last_updated": datetime.utcnow(),
    },
    {
        "call_sign": "HAZMAT-ECHO-09",
        "type": "Hazmat Team",
        "status": "AVAILABLE",
        "capacity": 4,
        "contact_phone": "+91-9876543214",
        "station_name": "Industrial Safety Depot",
        "assigned_incident_id": None,
        "location": {"type": "Point", "coordinates": [77.6750, 12.8450]},
        "address": "Electronic City Phase 2, Bangalore",
        "last_updated": datetime.utcnow(),
    }
]


async def seed_database():
    print(f"Connecting to MongoDB at {MONGODB_URL} (db: {MONGODB_DB_NAME})...")
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    db = client[MONGODB_DB_NAME]

    try:
        # Check connection
        await client.admin.command("ping")
        print("Connected successfully.")

        # Ensure 2dsphere indexes
        print("Creating geospatial indexes...")
        await db.incidents.create_index([("location.coordinates", "2dsphere")])
        await db.resources.create_index([("location.coordinates", "2dsphere")])

        # Seed resources
        print(f"Seeding {len(SAMPLE_RESOURCES)} emergency response units...")
        for resource in SAMPLE_RESOURCES:
            await db.resources.update_one(
                {"call_sign": resource["call_sign"]},
                {"$set": resource},
                upsert=True
            )

        print("Seeding complete! Emergency units registered successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
