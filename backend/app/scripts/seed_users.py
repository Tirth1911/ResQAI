import os
import asyncio
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.config import settings
from backend.app.database import DatabaseManager
from backend.app.models.user import UserRole
from backend.app.utils.security import hash_password

logger = logging.getLogger("resqai.seed_users")

DEFAULT_DEMO_USERS = [
    {
        "user_id": "USR-ADMIN-001",
        "email": "admin@resqai.org",
        "full_name": "Commander Sarah Jenkins",
        "role": UserRole.ADMIN.value,
        "department": "Emergency Management Command Executive",
        "phone": "+91 98765 43210",
        "env_pwd_var": "DEMO_ADMIN_PASSWORD"
    },
    {
        "user_id": "USR-DISP-002",
        "email": "dispatcher@resqai.org",
        "full_name": "Captain Marcus Vance",
        "role": UserRole.DISPATCHER.value,
        "department": "Central 911 Operations & Tactical Dispatch",
        "phone": "+91 98765 43211",
        "env_pwd_var": "DEMO_DISPATCHER_PASSWORD"
    },
    {
        "user_id": "USR-FIELD-003",
        "email": "field@resqai.org",
        "full_name": "Lieutenant David Ramos",
        "role": UserRole.FIELD_TEAM.value,
        "department": "Rapid Emergency Response Squad Lead",
        "phone": "+91 98765 43212",
        "env_pwd_var": "DEMO_FIELD_PASSWORD"
    },
    {
        "user_id": "USR-HOSP-004",
        "email": "hospital@resqai.org",
        "full_name": "Dr. Ananya Sharma",
        "role": UserRole.HOSPITAL.value,
        "department": "Level-1 Trauma Center Medical Director",
        "phone": "+91 98765 43213",
        "env_pwd_var": "DEMO_HOSPITAL_PASSWORD"
    },
    {
        "user_id": "USR-VIEW-005",
        "email": "viewer@resqai.org",
        "full_name": "Auditor Elena Rostova",
        "role": UserRole.VIEWER.value,
        "department": "Public Safety Compliance & Observer",
        "phone": "+91 98765 43214",
        "env_pwd_var": "DEMO_VIEWER_PASSWORD"
    }
]


async def seed_demo_users(db: AsyncIOMotorDatabase) -> int:
    """
    Seed or update the 5 standard demo accounts in MongoDB.
    Passwords are read from environment variables or fall back to default development password.
    """
    seeded_count = 0
    now = datetime.now(timezone.utc)

    # Ensure unique index on email and user_id
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("user_id", unique=True)
    except Exception as e:
        logger.warning(f"User index creation notice: {e}")

    for u in DEFAULT_DEMO_USERS:
        # Read password securely from environment variable or settings
        raw_password = os.getenv(u["env_pwd_var"]) or os.getenv("DEMO_DEFAULT_PASSWORD") or settings.DEMO_DEFAULT_PASSWORD
        hashed = hash_password(raw_password)

        user_doc = {
            "user_id": u["user_id"],
            "email": u["email"].lower().strip(),
            "full_name": u["full_name"],
            "role": u["role"],
            "department": u["department"],
            "phone": u["phone"],
            "hashed_password": hashed,
            "is_active": True,
            "updated_at": now
        }

        # Upsert user document
        existing = await db.users.find_one({"email": user_doc["email"]})
        if not existing:
            user_doc["created_at"] = now
            await db.users.insert_one(user_doc)
            seeded_count += 1
        else:
            # Update password hash and role
            await db.users.update_one(
                {"email": user_doc["email"]},
                {"$set": {
                    "hashed_password": hashed,
                    "role": u["role"],
                    "full_name": u["full_name"],
                    "department": u["department"],
                    "is_active": True,
                    "updated_at": now
                }}
            )
            seeded_count += 1

    logger.info(f"Seeded {seeded_count} demo user accounts into MongoDB.")
    return seeded_count


if __name__ == "__main__":
    async def main():
        db = await DatabaseManager.get_database()
        count = await seed_demo_users(db)
        print(f"Successfully seeded {count} demo accounts!")
        await DatabaseManager.close_mongo_connection()

    asyncio.run(main())
