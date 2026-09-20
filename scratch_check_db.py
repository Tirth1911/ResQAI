import asyncio
from backend.app.db.mongodb import connect_to_mongo, get_db

async def main():
    await connect_to_mongo()
    db = get_db()
    total = await db.incidents.count_documents({})
    print("Total incidents:", total)
    cursor = db.incidents.find({})
    async for inc in cursor:
        print(inc.get("incident_id"), "|", inc.get("title"), "|", inc.get("status"), "|", inc.get("severity"))

if __name__ == "__main__":
    asyncio.run(main())
