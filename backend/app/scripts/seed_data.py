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
        "resource_id": "RES-108-SOLA",
        "name": "108 Trauma Unit - Sola Civil",
        "category": ResourceCategory.AMBULANCE.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["AMBULANCE", "ALS", "TRAUMA", "PARAMEDIC", "108"],
        "location": {"type": "Point", "coordinates": [72.5283, 23.0768]},
        "address": "Sola Civil Hospital, SG Highway, Ahmedabad",
        "location_name": "Sola Civil Hospital",
        "capacity": 4,
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-POL-USMAN",
        "name": "Patrol Unit 4 - Usmanpura",
        "category": ResourceCategory.POLICE.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["POLICE", "CROWD_CONTROL", "CORDON", "GREEN_CORRIDOR"],
        "location": {"type": "Point", "coordinates": [72.5694, 23.0446]},
        "address": "Usmanpura Traffic Circle, Ahmedabad",
        "location_name": "Usmanpura Sector Outpost",
        "capacity": 2,
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-FIR-NARODA",
        "name": "Fire Rescue Engine 02 - Naroda",
        "category": ResourceCategory.FIRE_TRUCK.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["FIRE_TRUCK", "FOAM_TENDER", "HAZMAT", "EXTRICATION"],
        "location": {"type": "Point", "coordinates": [72.6450, 23.0680]},
        "address": "Naroda GIDC Fire Station, Ahmedabad",
        "location_name": "Naroda Fire Station",
        "capacity": 6,
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-DRN-GANDHI",
        "name": "Drone Recon Alpha - Gandhinagar",
        "category": ResourceCategory.DISASTER_TEAM.value,
        "status": ResourceStatus.AVAILABLE.value,
        "capabilities": ["DRONE", "RECON", "THERMAL_IMAGING", "GAS_DETECTION"],
        "location": {"type": "Point", "coordinates": [72.6369, 23.2156]},
        "address": "Gandhinagar Emergency Operations Center",
        "location_name": "Gandhinagar Command Hub",
        "capacity": 1,
        "current_incident_id": None,
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "resource_id": "RES-HAZ-VATVA",
        "name": "HAZMAT Decon Unit 01 - Vatva",
        "category": ResourceCategory.DISASTER_TEAM.value,
        "status": ResourceStatus.BUSY.value,
        "capabilities": ["HAZMAT", "CHEMICAL_NEUTRALIZATION", "DECONTAMINATION"],
        "location": {"type": "Point", "coordinates": [72.6280, 22.9650]},
        "address": "Vatva GIDC Industrial Emergency Station",
        "location_name": "Vatva HAZMAT Center",
        "capacity": 5,
        "current_incident_id": "inc-001",
        "updated_at": datetime.now(timezone.utc)
    }
]

SAMPLE_HOSPITALS = [
    {
        "hospital_id": "HOSP-SOLA",
        "name": "Sola Civil Hospital & Trauma Center",
        "status": HospitalStatus.OPEN.value,
        "emergency_beds_total": 50,
        "emergency_beds_available": 22,
        "icu_beds_total": 20,
        "icu_beds_available": 8,
        "trauma_bay_ready": True,
        "location": {"type": "Point", "coordinates": [72.5283, 23.0768]},
        "address": "SG Highway, Sola, Ahmedabad",
        "phone": "+91 79 2766 2200",
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "hospital_id": "HOSP-CIVIL",
        "name": "Ahmedabad Civil Hospital - Asarwa",
        "status": HospitalStatus.OPEN.value,
        "emergency_beds_total": 120,
        "emergency_beds_available": 45,
        "icu_beds_total": 40,
        "icu_beds_available": 14,
        "trauma_bay_ready": True,
        "location": {"type": "Point", "coordinates": [72.6025, 23.0512]},
        "address": "Asarwa, Ahmedabad",
        "phone": "+91 79 2268 0074",
        "updated_at": datetime.now(timezone.utc)
    }
]

SAMPLE_INCIDENTS = [
    {
        "incident_id": "inc-001",
        "title": "Major Chemical Storage Tanker Fire & Gas Leak",
        "description": "Extracted high risk of hazardous chemical cloud spread, structural fire, and 10+ potential casualties. Classified as Critical Industrial HAZMAT event requiring foam tender + decon unit + 108 ALS.",
        "type": "industrial_hazard",
        "severity": "CRITICAL",
        "priority": "P1",
        "status": "VERIFIED",
        "confidence": 0.98,
        "source": "iot_sensor",
        "location": {"type": "Point", "coordinates": [72.6582, 23.0135]},
        "address": "Phase 3, Odhav GIDC Industrial Estate, Ahmedabad",
        "reported_at": datetime.now(timezone.utc) - timedelta(minutes=10),
        "updated_at": datetime.now(timezone.utc) - timedelta(minutes=10),
        "assigned_resources": [],
        "duplicate_count": 3,
        "ai_analysis": {
            "summary": "Extracted high risk of hazardous chemical cloud spread, structural fire, and 10+ potential casualties. Classified as Critical Industrial HAZMAT event requiring foam tender + decon unit + 108 ALS.",
            "reasoning": "Chemical cloud spread threat to nearby residential sectors. Rapid foam containment and 108 trauma support required.",
            "people_at_risk": "10+ Persons",
            "incident_type": "industrial_hazard",
            "confidence": 0.98,
            "immediate_actions": [
                "Evacuate 1km downwind radius immediately",
                "Deploy heavy chemical foam tender & decon unit",
                "Establish green corridor to Sola Civil Trauma Center"
            ]
        },
        "timeline": [
            {"timestamp": datetime.now(timezone.utc) - timedelta(minutes=10), "action": "HAZMAT Sensor Triggered", "actor": "Sensor #88 - Odhav GIDC", "details": "High chemical gas density detected."},
            {"timestamp": datetime.now(timezone.utc) - timedelta(minutes=6), "action": "AI Classified Critical HAZMAT", "actor": "AI Triage Engine", "details": "Priority score 100/100, 1km radius warning."}
        ]
    },
    {
        "incident_id": "inc-002",
        "title": "SG Highway Express Multi-Vehicle Collision",
        "description": "3 passenger vehicles involved in high-speed collision near Iskcon Flyover. Traffic blockade and minor injuries.",
        "type": "road_accident",
        "severity": "HIGH",
        "priority": "P2",
        "status": "DISPATCHED",
        "confidence": 0.91,
        "source": "citizen_call",
        "location": {"type": "Point", "coordinates": [72.5085, 23.0274]},
        "address": "Iskcon Flyover, SG Highway, Ahmedabad",
        "reported_at": datetime.now(timezone.utc) - timedelta(minutes=25),
        "updated_at": datetime.now(timezone.utc) - timedelta(minutes=25),
        "assigned_resources": ["RES-POL-USMAN"],
        "duplicate_count": 1
    },
    {
        "incident_id": "inc-003",
        "title": "Residential Complex Electrical Transformer Spark & Fire",
        "description": "Sparking transformer causing local blackout and small tree fire near Usmanpura.",
        "type": "fire",
        "severity": "MEDIUM",
        "priority": "P3",
        "status": "REPORTED",
        "confidence": 0.85,
        "source": "citizen_call",
        "location": {"type": "Point", "coordinates": [72.5650, 23.0410]},
        "address": "Usmanpura Cross Roads, Ahmedabad",
        "reported_at": datetime.now(timezone.utc) - timedelta(minutes=40),
        "updated_at": datetime.now(timezone.utc) - timedelta(minutes=40),
        "assigned_resources": [],
        "duplicate_count": 0
    },
    {
        "incident_id": "inc-004",
        "title": "Sabarmati Riverfront Walkway Medical Distress",
        "description": "Senior citizen experiencing acute chest pain during morning walk.",
        "type": "medical_emergency",
        "severity": "MEDIUM",
        "priority": "P2",
        "status": "VERIFIED",
        "confidence": 0.94,
        "source": "emergency_hotline",
        "location": {"type": "Point", "coordinates": [72.5780, 23.0320]},
        "address": "Sabarmati Riverfront East Promenade, Ahmedabad",
        "reported_at": datetime.now(timezone.utc) - timedelta(minutes=15),
        "updated_at": datetime.now(timezone.utc) - timedelta(minutes=15),
        "assigned_resources": [],
        "duplicate_count": 0
    },
    {
        "incident_id": "inc-005",
        "title": "Commercial Warehouse Roof Structural Strain",
        "description": "Heavy rainfall accumulation causing structural roof sag in Asarwa industrial shed.",
        "type": "building_collapse",
        "severity": "LOW",
        "priority": "P4",
        "status": "REPORTED",
        "confidence": 0.82,
        "source": "citizen_call",
        "location": {"type": "Point", "coordinates": [72.6100, 23.0550]},
        "address": "Asarwa Industrial Area, Ahmedabad",
        "reported_at": datetime.now(timezone.utc) - timedelta(minutes=50),
        "updated_at": datetime.now(timezone.utc) - timedelta(minutes=50),
        "assigned_resources": [],
        "duplicate_count": 0
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

