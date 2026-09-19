import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.config import settings

logger = logging.getLogger("resqai.database")


class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect_to_mongo(cls) -> AsyncIOMotorDatabase:
        """Establish asynchronous connection to MongoDB (Atlas or Local) and ensure all collection indexes."""
        if cls.db is not None:
            return cls.db

        try:
            uri = settings.mongo_uri
            db_name = settings.mongo_db_name
            logger.info(f"Connecting to MongoDB database '{db_name}' ...")
            cls.client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=5000
            )
            cls.db = cls.client[db_name]
            
            # Verify connectivity with ping
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB Atlas / Instance database: {db_name}")
            
            # Ensure all required 2dsphere and query indexes
            await cls.init_indexes()

            # Seed demo user accounts (ADMIN, DISPATCHER, FIELD_TEAM, HOSPITAL, VIEWER)
            try:
                from backend.app.scripts.seed_users import seed_demo_users
                await seed_demo_users(cls.db)
            except Exception as seed_err:
                logger.warning(f"User seed warning: {seed_err}")

            return cls.db
        except Exception as e:
            logger.warning(
                f"Failed to connect to MongoDB: {e}. "
                f"Application will run, but database features require active MongoDB instance."
            )
            if cls.client is not None and cls.db is not None:
                return cls.db
            raise

    @classmethod
    async def close_mongo_connection(cls) -> None:
        """Close MongoDB connection gracefully."""
        if cls.client is not None:
            logger.info("Closing MongoDB connection...")
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB connection closed.")

    @classmethod
    async def init_indexes(cls) -> None:
        """Ensure MongoDB 2dsphere and search indexes exist for all 8 collections."""
        if cls.db is None:
            return
        try:
            # 1. Incidents Collection Indexes
            await cls.db.incidents.create_index([("location", "2dsphere")])
            await cls.db.incidents.create_index([("incident_id", 1)], unique=True)
            await cls.db.incidents.create_index([("status", 1)])
            await cls.db.incidents.create_index([("severity", 1)])
            await cls.db.incidents.create_index([("priority", 1)])
            await cls.db.incidents.create_index([("type", 1)])
            await cls.db.incidents.create_index([("reported_at", -1)])
            await cls.db.incidents.create_index([("status", 1), ("priority", 1), ("reported_at", -1)])

            # 2. Resources Collection Indexes
            await cls.db.resources.create_index([("location", "2dsphere")])
            await cls.db.resources.create_index([("resource_id", 1)], unique=True)
            await cls.db.resources.create_index([("status", 1)])
            await cls.db.resources.create_index([("category", 1)])

            # 3. Teams Collection Indexes
            await cls.db.teams.create_index([("location", "2dsphere")])
            await cls.db.teams.create_index([("team_id", 1)], unique=True)
            await cls.db.teams.create_index([("status", 1)])
            await cls.db.teams.create_index([("type", 1)])

            # 4. Hospitals Collection Indexes
            await cls.db.hospitals.create_index([("location", "2dsphere")])
            await cls.db.hospitals.create_index([("hospital_id", 1)], unique=True)
            await cls.db.hospitals.create_index([("status", 1)])

            # 5. Notifications Collection Indexes
            await cls.db.notifications.create_index([("notification_id", 1)], unique=True)
            await cls.db.notifications.create_index([("created_at", -1)])
            await cls.db.notifications.create_index([("read", 1)])

            # 6. Users Collection Indexes
            await cls.db.users.create_index([("user_id", 1)], unique=True)
            await cls.db.users.create_index([("email", 1)], unique=True)

            # 7. Incident Updates Collection Indexes
            await cls.db.incident_updates.create_index([("update_id", 1)], unique=True)
            await cls.db.incident_updates.create_index([("incident_id", 1), ("created_at", -1)])

            # 8. Analytics Collection Indexes
            await cls.db.analytics.create_index([("timestamp", -1)])

            logger.info("All 8 MongoDB collections and 2dsphere indexes verified successfully.")
        except Exception as err:
            logger.warning(f"Index initialization warning: {err}")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Retrieve database instance."""
        if cls.db is None:
            # Auto-instantiate if called before lifespan
            uri = settings.mongo_uri
            db_name = settings.mongo_db_name
            cls.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            cls.db = cls.client[db_name]
        return cls.db

    @classmethod
    async def is_healthy(cls) -> bool:
        """Check if MongoDB Atlas or local connection is healthy."""
        try:
            db = cls.get_db()
            if cls.client is not None:
                await cls.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False


# Dependency injection helper for FastAPI routes
async def get_database() -> AsyncIOMotorDatabase:
    return DatabaseManager.get_db()
