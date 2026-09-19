from unittest.mock import AsyncMock, patch
import httpx
import pytest
from httpx import AsyncClient

from app.config import settings
from app.models import IncidentSeverity, IncidentType
from app.services.triage import _triage_cache, rules_triage, triage


@pytest.mark.asyncio
async def test_rules_triage_8_sample_cases():
    """
    Test 8 sample cases for rule-based triage:
    - 5 types: fire, flood, accident, medical, industrial
    - 3 severity cases: critical, low, high
    """
    test_cases = [
        # 1. Fire
        {
            "text": "Thick black smoke and burning flames spotted on commercial roof.",
            "source": "citizen",
            "expected_type": IncidentType.FIRE,
            "expected_severity": None,
        },
        # 2. Flood
        {
            "text": "Underpass submerged in water after severe downpour, water level rising rapidly.",
            "source": "citizen",
            "expected_type": IncidentType.FLOOD,
            "expected_severity": None,
        },
        # 3. Accident
        {
            "text": "Car collision and overturned truck blocking two highway lanes.",
            "source": "call_center",
            "expected_type": IncidentType.ACCIDENT,
            "expected_severity": None,
        },
        # 4. Medical
        {
            "text": "Elderly patient collapsed unconscious experiencing severe chest pain.",
            "source": "call_center",
            "expected_type": IncidentType.MEDICAL,
            "expected_severity": None,
        },
        # 5. Industrial
        {
            "text": "Factory chemical boiler solvent leakage emitting toxic fumes.",
            "source": "field_team",
            "expected_type": IncidentType.INDUSTRIAL,
            "expected_severity": None,
        },
        # 6. Critical severity booster case
        {
            "text": "Massive chemical explosion with multiple casualties trapped inside.",
            "source": "citizen",
            "expected_type": IncidentType.INDUSTRIAL,
            "expected_severity": IncidentSeverity.CRITICAL,
            "expected_priority": 1,
        },
        # 7. Low severity reducer case
        {
            "text": "Small minor roadside cardboard spark, completely contained, no injuries.",
            "source": "citizen",
            "expected_type": IncidentType.FIRE,
            "expected_severity": IncidentSeverity.LOW,
            "expected_priority": 4,
        },
        # 8. High severity booster case
        {
            "text": "Spreading blaze threatening nearby residential apartments.",
            "source": "citizen",
            "expected_type": IncidentType.FIRE,
            "expected_severity": IncidentSeverity.HIGH,
            "expected_priority": 2,
        },
    ]

    for tc in test_cases:
        res = rules_triage(tc["text"], tc["source"])
        assert res.classified_by == "rules"
        assert res.type == tc["expected_type"], f"Expected {tc['expected_type']} for '{tc['text']}', got {res.type}"
        if tc.get("expected_severity"):
            assert res.severity == tc["expected_severity"], f"Expected {tc['expected_severity']} for '{tc['text']}', got {res.severity}"
        if tc.get("expected_priority"):
            assert res.priority == tc["expected_priority"]


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_rules(monkeypatch):
    """Verify that when LLM fails (network timeout or HTTP error), triage falls back gracefully to rules."""
    monkeypatch.setattr(settings, "LLM_API_KEY", "mock-groq-key")

    _triage_cache.clear()

    # Mock AsyncClient.post to raise a ConnectTimeout exception
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectTimeout("Connection timed out")):
        res = await triage(
            text="Explosion in chemical storage unit with casualties trapped.",
            source="citizen",
        )

        assert res.classified_by == "rules"
        assert res.type == IncidentType.INDUSTRIAL
        assert res.severity == IncidentSeverity.CRITICAL
        assert res.priority == 1
        assert res.confidence == 0.60


@pytest.mark.asyncio
async def test_triage_lru_cache():
    """Verify in-memory LRU cache stores triage results without redundant processing."""
    _triage_cache.clear()

    text = "Car crash on SG Highway"
    source = "citizen"

    # First call - populates cache
    res1 = await triage(text=text, source=source)
    assert res1.classified_by == "rules"
    assert res1.type == IncidentType.ACCIDENT

    cache_key = f"{source}:{text.strip().lower()}"
    assert cache_key in _triage_cache

    # Second call - retrieves from cache
    res2 = await triage(text=text, source=source)
    assert res2 == res1


@pytest.mark.asyncio
async def test_api_report_triage_integration(async_client: AsyncClient):
    """Verify POST /api/reports uses triage result to populate type, severity, priority, and status='triaged'."""
    resp = await async_client.post(
        "/api/reports",
        json={
            "source": "citizen",
            "text": "Severe chemical gas leak in warehouse.",
            "lat": 23.0640,
            "lng": 72.6610,
        },
    )
    assert resp.status_code == 201
    data = resp.json()["incident"]

    assert data["type"] == "industrial"
    assert data["status"] == "triaged"
    assert data["classified_by"] == "rules"
    assert data["ai_confidence"] is not None
    assert data["ai_reasoning"] is not None
