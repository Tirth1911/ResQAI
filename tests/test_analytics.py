import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.database import DatabaseManager
from backend.app.scripts.seed_data import seed_master_database
from backend.app.routers.analytics import (
    get_summary_pipeline_data,
    get_types_pipeline_data,
    get_regions_pipeline_data,
    get_response_times_pipeline_data,
    get_utilization_pipeline_data,
    get_shortages_pipeline_data,
    get_timeline_pipeline_data,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    DatabaseManager.client = None
    DatabaseManager.db = None
    db = await DatabaseManager.connect_to_mongo()
    await db.incidents.delete_many({})
    await db.resources.delete_many({})
    await db.assignments.delete_many({})
    await db.alerts.delete_many({})
    await db.hospitals.delete_many({})
    await seed_master_database(db)


@pytest.mark.asyncio
async def test_analytics_pipelines_direct():
    db = DatabaseManager.get_db()

    # 1. Summary
    summary = await get_summary_pipeline_data(db)
    assert "active_incidents" in summary
    assert "resolved_today" in summary
    assert "avg_response_time_minutes" in summary
    assert "resources_available" in summary
    assert "resources_busy" in summary

    # 2. Types
    types = await get_types_pipeline_data(db)
    assert isinstance(types, list)
    assert len(types) > 0

    # 3. Regions
    regions = await get_regions_pipeline_data(db)
    assert "grid" in regions
    assert "frequently_affected_locations" in regions
    assert len(regions["frequently_affected_locations"]) <= 5

    # 4. Response Times
    resp_times = await get_response_times_pipeline_data(db)
    assert isinstance(resp_times, list)

    # 5. Utilization
    util = await get_utilization_pipeline_data(db)
    assert isinstance(util, list)

    # 6. Shortages
    shortages = await get_shortages_pipeline_data(db)
    assert isinstance(shortages, list)

    # 7. Timeline
    timeline = await get_timeline_pipeline_data(db)
    assert isinstance(timeline, list)
    assert len(timeline) == 15  # 14 days ago up to today = 15 points


@pytest.mark.asyncio
async def test_analytics_endpoints_http():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_summary = await ac.get("/api/analytics/summary")
        assert res_summary.status_code == 200
        assert "active_incidents" in res_summary.json()

        res_types = await ac.get("/api/analytics/types")
        assert res_types.status_code == 200
        assert isinstance(res_types.json(), list)

        res_regions = await ac.get("/api/analytics/regions")
        assert res_regions.status_code == 200
        assert "grid" in res_regions.json()

        res_times = await ac.get("/api/analytics/response-times")
        assert res_times.status_code == 200

        res_util = await ac.get("/api/analytics/utilization")
        assert res_util.status_code == 200

        res_short = await ac.get("/api/analytics/shortages")
        assert res_short.status_code == 200

        res_line = await ac.get("/api/analytics/timeline")
        assert res_line.status_code == 200
        assert len(res_line.json()) == 15
