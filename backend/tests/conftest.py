from typing import AsyncGenerator
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import settings
from app.db import ensure_indexes, get_client, get_db
from app.main import app

TEST_DB_NAME = "resqai_test"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _cleanup_test_database_session() -> AsyncGenerator[None, None]:
    """Configure settings to use test database, and drop it after the test session."""
    orig_db = settings.MONGODB_DB
    settings.MONGODB_DB = TEST_DB_NAME
    yield
    client = get_client()
    try:
        await client.drop_database(TEST_DB_NAME)
    finally:
        await client.close()
    settings.MONGODB_DB = orig_db


@pytest_asyncio.fixture
async def test_db() -> AsyncDatabase:
    """Function-scoped test database fixture ensuring indexes on test database."""
    await ensure_indexes(TEST_DB_NAME)
    return get_db(TEST_DB_NAME)


@pytest_asyncio.fixture
async def async_client(test_db: AsyncDatabase) -> AsyncGenerator[AsyncClient, None]:
    """HTTP async client configured against FastAPI application using test database."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
