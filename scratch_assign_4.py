import asyncio
from backend.app.database import DatabaseManager

async def assign():
    db = await DatabaseManager.connect_to_mongo()
    await db.incidents.update_one(
        {"incident_id": "inc-001"},
        {"$set": {"assigned_resources": ["RES-FIR-NAVRANG", "RES-POL-USMAN", "RES-FIR-NARODA", "RES-NDRF-GANDHI"]}}
    )
    # Set those 4 resources to BUSY/DISPATCHED
    await db.resources.update_many(
        {"resource_id": {"$in": ["RES-FIR-NAVRANG", "RES-POL-USMAN", "RES-FIR-NARODA", "RES-NDRF-GANDHI"]}},
        {"$set": {"status": "BUSY", "current_incident_id": "inc-001"}}
    )
    print("Assigned 4 units to inc-001")
    await DatabaseManager.close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(assign())
