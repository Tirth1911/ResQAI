import asyncio
from backend.app.database import DatabaseManager

async def run():
    db = await DatabaseManager.connect_to_mongo()
    res = await db.incidents.update_one(
        {"incident_id": "inc-001"},
        {"$set": {"assigned_resources": ["RES-FIR-NARODA", "RES-108-SOLA", "RES-POL-USMAN", "RES-DRN-GANDHI", "RES-HAZ-VATVA"]}}
    )
    print("Modified count:", res.modified_count)
    await DatabaseManager.close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run())
