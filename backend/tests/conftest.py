from typing import AsyncGenerator
import pytest_asyncio
from pymongo.asynchronous.database import AsyncDatabase

from app.db import ensure_indexes, get_client, get_db

TEST_DB_NAME = "resqai_test"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _cleanup_test_database_session() -> AsyncGenerator[None, None]:
    """Clean up the test database after the test session finishes."""
    yield
    client = get_client()
    try:
        await client.drop_database(TEST_DB_NAME)
    finally:
        await client.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncDatabase:
    """Function-scoped test database fixture ensuring indexes on test database."""
    await ensure_indexes(TEST_DB_NAME)
    return get_db(TEST_DB_NAME)
