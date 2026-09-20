import asyncio
from backend.app.database import DatabaseManager

async def check():
    db = await DatabaseManager.connect_to_mongo()
    cursor = db.resources.find({})
    async for r in cursor:
        print(f"{r.get('resource_id')} | {r.get('name')} | {r.get('category')} | {r.get('location', {}).get('coordinates')}")
    await DatabaseManager.close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check())
