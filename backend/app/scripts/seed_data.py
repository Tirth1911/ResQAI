import asyncio
import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.database import DatabaseManager
from backend.app.models.incident import IncidentType, IncidentSeverity, IncidentPriority, IncidentStatus, IncidentSource
from backend.app.models.resource import ResourceCategory, ResourceStatus
from backend.app.models.hospital import HospitalStatus
from backend.app.scripts.seed_users import seed_demo_users

logger = logging.getLogger("resqai.seed_data")

SAMPLE_RESOURCES = [
    {
        "resource_id": "RES-AMB-01",
        "name": "Advanced Life Support Ambulance 01",
        "category": ResourceCategory.AMBULANCE.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["AMBULANCE", "ALS", "AED", "VENTILATOR", "PARAMEDIC", "TRAUMA_KIT"],
        "location": {"type": "Point", "coordinates": [77.5946, 12.9716]},
        "address": "Victoria Hospital Trauma Wing, Bangalore",
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-AMB-02",
        "name": "Rapid Cardiac Ambulance 02",
        "category": ResourceCategory.AMBULANCE.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["AMBULANCE", "AED", "ICU_TRANSPORT", "PARAMEDIC"],
        "location": {"type": "Point", "coordinates": [77.6101, 12.9165]},
        "address": "BTM Layout Emergency Dispatch Bay",
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-FIR-01",
        "name": "Heavy Hydraulic Extrication Fire Engine 01",
        "category": ResourceCategory.FIRE_TRUCK.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["FIRE_TRUCK", "HYDRAULIC_CUTTERS", "EXTRICATION", "WATER_BOWSER", "FOAM_SUPPRESSION"],
        "location": {"type": "Point", "coordinates": [77.6245, 12.9352]},
        "address": "Koramangala Fire Station",
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-FIR-02",
        "name": "50-Meter Aerial Ladder Platform 02",
        "category": ResourceCategory.FIRE_TRUCK.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["FIRE_TRUCK", "AERIAL_LADDER", "HIGH_RISE_RESCUE", "FOAM_CANNONS"],
        "location": {"type": "Point", "coordinates": [77.6745, 12.9252]},
        "address": "Bellandur Outer Ring Road Depot",
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-POL-01",
        "name": "Traffic Police Rapid Interceptor 01",
        "category": ResourceCategory.POLICE.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["POLICE", "TRAFFIC_DIVERSION", "CROWD_CONTROL", "GREEN_CORRIDOR"],
        "location": {"type": "Point", "coordinates": [77.6408, 12.9783]},
        "address": "Indiranagar Traffic Control Sector",
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-POL-02",
        "name": "Highway Patrol Cruiser 02",
        "category": ResourceCategory.POLICE.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["POLICE", "HIGHWAY_PATROL", "RADAR", "FIRST_AID"],
        "location": {"type": "Point", "coordinates": [77.6620, 12.9350]},
        "address": "Sarjapur Road Junction Post",
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-HAZ-01",
        "name": "Specialized HAZMAT Chemical Unit 01",
        "category": ResourceCategory.DISASTER_TEAM.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["HAZMAT", "SCBA", "CHEMICAL_NEUTRALIZATION", "GAS_DETECTION", "DECONTAMINATION"],
        "location": {"type": "Point", "coordinates": [77.5308, 13.0283]},
        "address": "Peenya Industrial Defense Station",
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-BOT-01",
        "name": "Motorized Inflatable Flood Rescue Boat 01",
        "category": ResourceCategory.RESCUE_TEAM.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["RESCUE_BOAT", "WATER_RESCUE", "DIVING", "SONAR", "LIFE_JACKETS"],
        "location": {"type": "Point", "coordinates": [77.6150, 12.9120]},
        "address": "Madiwala Lake Water Rescue Outpost",
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    }
]

SAMPLE_HOSPITALS = [
    {
        "hospital_id": "HOSP-001",
        "name": "St. John's Level-1 Trauma Hospital",
        "status": HospitalStatus.OPEN.value,
        "emergency_beds_total": 45,
        "emergency_beds_available": 18,
        "icu_beds_total": 20,
        "icu_beds_available": 6,
        "trauma_bay_ready": True,
        "location": {"type": "Point", "coordinates": [77.6186, 12.9344]},
        "address": "Sarjapur Road, Koramangala, Bangalore",
        "phone": "+91 80 2206 5000",
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "hospital_id": "HOSP-002",
        "name": "Victoria Memorial Hospital Emergency Wing",
        "status": HospitalStatus.OPEN.value,
        "emergency_beds_total": 60,
        "emergency_beds_available": 24,
        "icu_beds_total": 25,
        "icu_beds_available": 8,
        "trauma_bay_ready": True,
        "location": {"type": "Point", "coordinates": [77.5746, 12.9625]},
        "address": "Fort Road, City Market, Bangalore",
        "phone": "+91 80 2670 1150",
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "hospital_id": "HOSP-003",
        "name": "Manipal Multi-Specialty Critical Care",
        "status": HospitalStatus.OPEN.value,
        "emergency_beds_total": 50,
        "emergency_beds_available": 12,
        "icu_beds_total": 18,
        "icu_beds_available": 4,
        "trauma_bay_ready": True,
        "location": {"type": "Point", "coordinates": [77.6514, 12.9587]},
        "address": "HAL Old Airport Road, Bangalore",
        "phone": "+91 80 2502 4444",
        "updated_at": datetime.now(timezone.utc)
    }
]


SAMPLE_INCIDENTS = [
    {
        "incident_id": "INC-20260919-0101",
        "title": "Major Highway Collision with Multiple Casualties",
        "description": "Multi-vehicle pileup involving an oil tanker and 3 passenger cars near Sarjapur Junction. Fuel spill detected, 4 passengers trapped.",
        "type": "road_accident",
        "severity": "CRITICAL",
        "priority": "P1",
        "status": "DISPATCHED",
        "confidence": 0.95,
        "source": "CITIZEN_CALL",
        "location": {"type": "Point", "coordinates": [77.6620, 12.9350]},
        "address": "Sarjapur Road Junction Expressway",
        "reported_at": datetime.now(timezone.utc) - timedelta(minutes=14),
        "assigned_resources": ["RES-AMB-01", "RES-POL-02"],
        "duplicate_count": 2,
        "related_incidents": [],
        "timeline": [
            {"timestamp": datetime.now(timezone.utc) - timedelta(minutes=14), "action": "Incident Reported", "actor": "Citizen 911 Call", "details": "Initial crash report with trapped passengers."},
            {"timestamp": datetime.now(timezone.utc) - timedelta(minutes=11), "action": "AI Classified P1 CRITICAL", "actor": "AI Triage Engine", "details": "Identified hazardous chemical hazard and multiple trauma victims."},
            {"timestamp": datetime.now(timezone.utc) - timedelta(minutes=8), "action": "Units Dispatched", "actor": "EOC Dispatcher", "details": "Dispatched ALS Ambulance 01 and Highway Patrol 02."}
        ]
    },
    {
        "incident_id": "INC-20260919-0102",
        "title": "Commercial Chemical Storage Facility Smoke Outbreak",
        "description": "Thick toxic smoke detected in Block B solvent warehouse. Automatic sprinkler alarm triggered, 2 security personnel evacuated.",
        "type": "fire",
        "severity": "HIGH",
        "priority": "P2",
        "status": "IN_PROGRESS",
        "confidence": 0.92,
        "source": "IOT_SENSOR",
        "location": {"type": "Point", "coordinates": [77.6745, 12.9252]},
        "address": "Bellandur Industrial Cluster, Outer Ring Road",
        "reported_at": datetime.now(timezone.utc) - timedelta(minutes=28),
        "assigned_resources": ["RES-FIR-02"],
        "duplicate_count": 1,
        "related_incidents": [],
        "timeline": [
            {"timestamp": datetime.now(timezone.utc) - timedelta(minutes=28), "action": "IoT Alarm Triggered", "actor": "Smoke Detector Sensor #41", "details": "High VOC and smoke optical density detected."},
            {"timestamp": datetime.now(timezone.utc) - timedelta(minutes=20), "action": "Fire Engine On Scene", "actor": "Ladder Platform 02", "details": "Cordon perimeter established, foam suppression active."}
        ]
    },
    {
        "incident_id": "INC-20260919-0103",
        "title": "Urban Low-Lying Residential Water Inundation",
        "description": "Storm drain overflow causing 3-foot waterlogging in residential basements. Elderly residents require transport assistance.",
        "type": "flood",
        "severity": "MEDIUM",
        "priority": "P3",
        "status": "VERIFIED",
        "confidence": 0.88,
        "source": "CITIZEN_CALL",
        "location": {"type": "Point", "coordinates": [77.6150, 12.9120]},
        "address": "Madiwala Lake Sector 2",
        "reported_at": datetime.now(timezone.utc) - timedelta(minutes=45),
        "assigned_resources": [],
        "duplicate_count": 0,
        "related_incidents": [],
        "timeline": [
            {"timestamp": datetime.now(timezone.utc) - timedelta(minutes=45), "action": "Incident Reported", "actor": "Citizen Call", "details": "Reported basement flooding and stranded residents."}
        ]
    }
]


async def seed_master_database(db: AsyncIOMotorDatabase, reset: bool = False) -> dict:
    """
    Seed standard resources, hospitals, users, and active incidents.
    Idempotent and safe to run multiple times.
    """
    if reset:
        logger.info("Reset flag provided. Dropping/clearing operational collections...")
        await db.incidents.delete_many({})
        await db.reports.delete_many({})
        await db.assignments.delete_many({})
        await db.alerts.delete_many({})
        await db.notifications.delete_many({})

    # 1. Seed Users
    users_count = await seed_demo_users(db)

    # 2. Seed Resources
    res_count = 0
    for r in SAMPLE_RESOURCES:
        await db.resources.update_one(
            {"resource_id": r["resource_id"]},
            {"$set": r},
            upsert=True
        )
        res_count += 1

    # 3. Seed Hospitals
    hosp_count = 0
    for h in SAMPLE_HOSPITALS:
        await db.hospitals.update_one(
            {"hospital_id": h["hospital_id"]},
            {"$set": h},
            upsert=True
        )
        hosp_count += 1

    # 4. Seed Active Incidents
    inc_count = 0
    for inc in SAMPLE_INCIDENTS:
        await db.incidents.update_one(
            {"incident_id": inc["incident_id"]},
            {"$set": inc},
            upsert=True
        )
        inc_count += 1

    logger.info(f"Seeded: {users_count} Users, {res_count} Resources, {hosp_count} Hospitals, {inc_count} Incidents.")
    return {
        "status": "database_seeded",
        "reset": reset,
        "users": users_count,
        "resources": res_count,
        "hospitals": hosp_count,
        "incidents": inc_count
    }


if __name__ == "__main__":
    import sys
    async def main():
        reset_flag = "--reset" in sys.argv
        db = await DatabaseManager.connect_to_mongo()
        res = await seed_master_database(db, reset=reset_flag)
        print("Seed result:", res)
        await DatabaseManager.close_mongo_connection()

    asyncio.run(main())

