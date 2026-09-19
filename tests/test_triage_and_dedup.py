import pytest
import pytest_asyncio
from unittest.mock import patch
import httpx
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.database import DatabaseManager
from backend.app.services.triage import triage, map_severity_to_priority


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Reset MongoDB client for test isolation."""
    DatabaseManager.client = None
    DatabaseManager.db = None
    db = await DatabaseManager.connect_to_mongo()
    # Clean test collections before each test run
    await db.incidents.delete_many({})
    await db.reports.delete_many({})


# =============================================================================
# STEP 4 TESTS: AI Triage & Rule-based Fallback
# =============================================================================
@pytest.mark.asyncio
async def test_rule_based_triage_eight_sample_texts():
    samples = [
        ("Heavy fire and smoke blazing at factory", "citizen", "fire"),
        ("Flash flood rising water level submerging street", "citizen", "flood"),
        ("Severe car crash and vehicle collision on highway", "citizen", "road_accident"),
        ("Patient unconscious experiencing cardiac arrest and chest pain", "citizen", "medical_emergency"),
        ("Toxic chemical gas leak at industrial chemical plant", "citizen", "gas_leak"),
        ("Explosion at oil refinery with multiple casualties and people trapped", "citizen", "critical"),
        ("Heavy fire burning apartment building", "citizen", "high"),
        ("Minor small oil spill with no injuries contained", "citizen", "low"),
    ]

    for text, source, expected in samples:
        res = await triage(text=text, source=source)
        assert res.classified_by == "rules"
        if expected in ["fire", "flood", "road_accident", "medical_emergency", "gas_leak", "industrial_hazard"]:
            assert res.type == expected
        elif expected in ["critical", "high", "low"]:
            assert res.severity == expected


@pytest.mark.asyncio
async def test_llm_failure_fallback_to_rules():
    with patch.object(httpx.AsyncClient, "post", side_effect=httpx.ConnectTimeout("LLM Timeout")):
        res = await triage(text="Fire blazes on residential block", source="citizen")
        assert res.classified_by == "rules"
        assert res.type == "fire"
        assert res.severity in ["high", "critical", "medium"]


# =============================================================================
# STEP 5 TESTS: Duplicate Detection & Merging
# =============================================================================
@pytest.mark.asyncio
async def test_dedup_same_fire_nearby_within_10min_merges():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Report 1
        r1 = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Building fire blazes near city center plaza",
            "lat": 37.7749,
            "lng": -122.4194
        })
        assert r1.status_code == 201
        d1 = r1.json()
        assert d1["merged"] is False
        master_id = d1["incident_id"]

        # Report 2 (within 300m and 5 minutes, different wording)
        r2 = await ac.post("/api/reports", json={
            "source": "citizen",
            "text": "Huge smoke and fire near city center plaza square",
            "lat": 37.7760,  # ~120m away
            "lng": -122.4190
        })
        assert r2.status_code == 201
        d2 = r2.json()
        assert d2["merged"] is True
        assert d2["incident_id"] == master_id
        assert d2["incident"]["report_count"] == 2


@pytest.mark.asyncio
async def test_dedup_same_text_5km_apart_does_not_merge():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Building fire blazes near city center plaza",
            "lat": 37.7749,
            "lng": -122.4194
        })
        assert r1.status_code == 201

        # Report 2 (5km away)
        r2 = await ac.post("/api/reports", json={
            "source": "citizen",
            "text": "Building fire blazes near city center plaza",
            "lat": 37.8200,  # ~5km away
            "lng": -122.4194
        })
        assert r2.status_code == 201
        assert r2.json()["merged"] is False


@pytest.mark.asyncio
async def test_dedup_different_types_same_place_does_not_merge():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Flash flood water level overflowing street",
            "lat": 37.7749,
            "lng": -122.4194
        })
        assert r1.status_code == 201
        assert r1.json()["incident"]["type"] == "flood"

        r2 = await ac.post("/api/reports", json={
            "source": "citizen",
            "text": "Vehicle crash and car collision at street intersection",
            "lat": 37.7749,
            "lng": -122.4194
        })
        assert r2.status_code == 201
        assert r2.json()["merged"] is False
        assert r2.json()["incident"]["type"] == "road_accident"


@pytest.mark.asyncio
async def test_third_report_bumps_severity():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1st Report (Low/Medium fire report)
        r1 = await ac.post("/api/reports", json={
            "source": "call_911",
            "text": "Small smoke near park entrance",
            "lat": 37.7749,
            "lng": -122.4194
        })
        inc_id = r1.json()["incident_id"]

        # 2nd Report (Merge)
        r2 = await ac.post("/api/reports", json={
            "source": "citizen",
            "text": "Small smoke near park entrance area",
            "lat": 37.7750,
            "lng": -122.4195
        })
        assert r2.json()["merged"] is True

        # 3rd Report (Merge -> triggers severity bump)
        r3 = await ac.post("/api/reports", json={
            "source": "field_unit",
            "text": "Small smoke near park entrance site",
            "lat": 37.7751,
            "lng": -122.4193
        })
        assert r3.json()["merged"] is True
        d3 = r3.json()["incident"]
        assert d3["report_count"] == 3
        assert d3["severity"].lower() in ["medium", "high", "critical"]

        # Check GET /api/incidents/{id}/reports endpoint
        rep_res = await ac.get(f"/api/incidents/{inc_id}/reports")
        assert rep_res.status_code == 200
        reports_list = rep_res.json()
        assert len(reports_list) == 3
