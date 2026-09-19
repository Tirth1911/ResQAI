import random
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase


async def generate_incident_id(db: AsyncIOMotorDatabase) -> str:
    """
    Generate unique human-readable incident identifier: INC-YYYYMMDD-XXXX
    e.g. INC-20260919-0001
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    prefix = f"INC-{date_str}-"

    # Find the latest incident for today to determine sequential counter
    latest_doc = await db.incidents.find_one(
        {"incident_id": {"$regex": f"^{prefix}"}},
        sort=[("incident_id", -1)]
    )

    if latest_doc and "incident_id" in latest_doc:
        try:
            last_seq = int(latest_doc["incident_id"].split("-")[-1])
            new_seq = last_seq + 1
        except Exception:
            new_seq = random.randint(1000, 9999)
    else:
        # Check total count today to ensure no collision
        count_today = await db.incidents.count_documents({"incident_id": {"$regex": f"^{prefix}"}})
        new_seq = count_today + 1

    candidate_id = f"{prefix}{new_seq:04d}"

    # Verify uniqueness
    while await db.incidents.find_one({"incident_id": candidate_id}):
        new_seq += 1
        candidate_id = f"{prefix}{new_seq:04d}"

    return candidate_id
