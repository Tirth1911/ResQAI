from typing import Any
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from backend.app.database import DatabaseManager


class DatabaseProxy:
    @property
    def db(self) -> AsyncIOMotorDatabase:
        return DatabaseManager.get_db()

    @property
    def incidents(self) -> AsyncIOMotorCollection:
        return DatabaseManager.get_db().incidents

    @property
    def reports(self) -> AsyncIOMotorCollection:
        return DatabaseManager.get_db().reports

    @property
    def resources(self) -> AsyncIOMotorCollection:
        return DatabaseManager.get_db().resources

    @property
    def assignments(self) -> AsyncIOMotorCollection:
        return DatabaseManager.get_db().assignments

    @property
    def hospitals(self) -> AsyncIOMotorCollection:
        return DatabaseManager.get_db().hospitals

    @property
    def alerts(self) -> AsyncIOMotorCollection:
        return DatabaseManager.get_db().alerts

    @property
    def users(self) -> AsyncIOMotorCollection:
        return DatabaseManager.get_db().users

    @property
    def notifications(self) -> AsyncIOMotorCollection:
        return DatabaseManager.get_db().notifications



db = DatabaseProxy()


def get_db() -> AsyncIOMotorDatabase:
    return DatabaseManager.get_db()
