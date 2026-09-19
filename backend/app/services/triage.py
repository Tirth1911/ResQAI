from collections import OrderedDict
import json
import logging
import re
from typing import Any, Literal, Optional
from httpx import AsyncClient, Limits, Timeout
from pydantic import BaseModel

from app.config import settings
from app.models import (
    IncidentSeverity,
    IncidentType,
    SEVERITY_PRIORITY_MAP,
)

logger = logging.getLogger("resqai.triage")

# In-memory LRU cache capacity
CACHE_MAX_SIZE = 1000
_triage_cache: OrderedDict[str, "TriageResult"] = OrderedDict()


class TriageResult(BaseModel):
    type: IncidentType
    severity: IncidentSeverity
    priority: int
    confidence: float
    reasoning: str
    classified_by: Literal["llm", "rules"]


# Keyword dictionaries for rule-based classification
TYPE_KEYWORDS: dict[IncidentType, list[str]] = {
    IncidentType.FIRE: [
        "fire", "smoke", "burning", "blaze", "flames", "cylinder",
        "tender", "spark", "combustion", "inferno",
    ],
    IncidentType.FLOOD: [
        "flood", "water level", "submerged", "overflow", "waterlogging",
        "inundation", "canal breach", "drain jam", "downpour", "deluge",
    ],
    IncidentType.ACCIDENT: [
        "crash", "collision", "accident", "overturned", "skidding",
        "hit and run", "derailed", "pileup", "vehicle", "traffic",
    ],
    IncidentType.MEDICAL: [
        "heart", "unconscious", "bleeding", "injured", "chest pain",
        "cardiac", "stroke", "collapse", "collapsed", "asthmatic",
        "respiratory", "anaphylaxis", "fracture", "heatstroke",
    ],
    IncidentType.INDUSTRIAL: [
        "gas leak", "chemical", "explosion", "factory", "toxic",
        "boiler", "solvent", "hazmat", "leakage", "radiation", "acid",
    ],
}

SEVERITY_BOOSTERS: list[str] = [
    "trapped", "explosion", "multiple", "children", "spreading",
    "casualties", "dead", "collapsed", "massive", "toxic", "fatal",
    "unconscious", "critical", "acute",
]

SEVERITY_REDUCERS: list[str] = [
    "minor", "small", "no injuries", "contained", "controlled",
    "superficial", "resolved", "low", "slight",
]


def _clean_json_string(content: str) -> str:
    """Strip markdown code fences and whitespace from LLM output."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        # Remove opening fence with optional language identifier
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    if cleaned.endswith("```"):
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def rules_triage(
    text: str,
    source: str,
    extra: Optional[dict[str, Any]] = None,
) -> TriageResult:
    """
    Deterministic rule-based triage classifier.
    Analyzes keywords, source telemetry, and severity boosters/reducers.
    """
    lower_text = text.lower()
    extra = extra or {}

    # 1. IoT Sensor Telemetry Overrides
    if source == "iot_sensor":
        sensor_type = str(extra.get("sensor", "")).lower()
        val = extra.get("value")
        try:
            numeric_val = float(val) if val is not None else None
        except (ValueError, TypeError):
            numeric_val = None

        if "smoke" in sensor_type or "fire" in sensor_type:
            severity = IncidentSeverity.HIGH
            if numeric_val is not None and numeric_val >= 800:
                severity = IncidentSeverity.CRITICAL
            elif numeric_val is not None and numeric_val < 300:
                severity = IncidentSeverity.MEDIUM
            return TriageResult(
                type=IncidentType.FIRE,
                severity=severity,
                priority=SEVERITY_PRIORITY_MAP[severity],
                confidence=0.85,
                reasoning=f"IoT smoke telemetry ({val} ppm) above critical threshold",
                classified_by="rules",
            )

        if "gas" in sensor_type or "chemical" in sensor_type:
            severity = IncidentSeverity.HIGH
            if numeric_val is not None and numeric_val >= 500:
                severity = IncidentSeverity.CRITICAL
            return TriageResult(
                type=IncidentType.INDUSTRIAL,
                severity=severity,
                priority=SEVERITY_PRIORITY_MAP[severity],
                confidence=0.85,
                reasoning="IoT hazardous chemical/gas sensor detection",
                classified_by="rules",
            )

        if "water" in sensor_type or "flood" in sensor_type:
            severity = IncidentSeverity.HIGH if (numeric_val and numeric_val > 1.0) else IncidentSeverity.MEDIUM
            return TriageResult(
                type=IncidentType.FLOOD,
                severity=severity,
                priority=SEVERITY_PRIORITY_MAP[severity],
                confidence=0.85,
                reasoning="IoT flood stage water-level sensor trigger",
                classified_by="rules",
            )

    # 2. Keyword Scoring for Type
    type_scores: dict[IncidentType, int] = {t: 0 for t in IncidentType}
    for inc_type, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower_text:
                type_scores[inc_type] += 1

    best_type = IncidentType.OTHER
    highest_score = 0
    for inc_type, score in type_scores.items():
        if score > highest_score:
            highest_score = score
            best_type = inc_type

    # 3. Severity Determination
    matched_boosters = [b for b in SEVERITY_BOOSTERS if b in lower_text]
    matched_reducers = [r for r in SEVERITY_REDUCERS if r in lower_text]

    # Check for hospital extra indicators
    if source == "hospital":
        if extra.get("incoming_casualties", 0) > 10 or extra.get("beds_available") == 0:
            matched_boosters.append("hospital_overflow")

    if len(matched_boosters) >= 2 or any(
        k in lower_text for k in ["explosion", "multiple casualties", "dead", "fatal", "mass casualty"]
    ):
        severity = IncidentSeverity.CRITICAL
    elif len(matched_boosters) >= 1:
        severity = IncidentSeverity.HIGH
    elif len(matched_reducers) >= 1 and not matched_boosters:
        severity = IncidentSeverity.LOW
    else:
        severity = IncidentSeverity.MEDIUM

    priority = SEVERITY_PRIORITY_MAP[severity]
    reasoning_parts = []
    if highest_score > 0:
        reasoning_parts.append(f"Keywords for {best_type.value}")
    if matched_boosters:
        reasoning_parts.append(f"Elevated by: {', '.join(matched_boosters[:2])}")
    elif matched_reducers:
        reasoning_parts.append(f"Lowered by: {', '.join(matched_reducers[:2])}")
    else:
        reasoning_parts.append("Standard default severity")

    reasoning = ". ".join(reasoning_parts)[:100]

    return TriageResult(
        type=best_type,
        severity=severity,
        priority=priority,
        confidence=0.60,
        reasoning=reasoning,
        classified_by="rules",
    )


async def _llm_triage(
    text: str,
    source: str,
    extra: Optional[dict[str, Any]] = None,
) -> Optional[TriageResult]:
    """
    Queries configured LLM API (Groq or OpenAI) for incident classification.
    Returns None on any network or parsing failure so caller can fall back.
    """
    if not settings.LLM_API_KEY:
        return None

    provider = (settings.LLM_PROVIDER or "groq").lower()
    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        model = settings.LLM_MODEL or "gpt-4o-mini"
    else:
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = settings.LLM_MODEL or "llama-3.3-70b-versatile"

    system_prompt = (
        "You are ResQAI, an emergency triage AI assistant for municipal dispatch. "
        "Analyze the report and output ONLY strict JSON with fields: "
        "'type', 'severity', 'confidence', 'reasoning'.\n"
        "Allowed types: 'fire', 'flood', 'accident', 'medical', 'industrial', 'other'.\n"
        "Allowed severities:\n"
        "- 'critical': Immediate threat to multiple lives, explosion, mass casualty, spreading fire in populated area.\n"
        "- 'high': Direct life threat, major structure damage, severe casualties.\n"
        "- 'medium': Contained danger, moderate property threat, non-fatal injuries.\n"
        "- 'low': Minor or no injuries, localized hazard.\n"
        "Constraint: 'confidence' must be float between 0.0 and 1.0. "
        "'reasoning' must be concise and under 25 words."
    )

    user_content = f"Source: {source}\nText: {text}"
    if extra:
        user_content += f"\nTelemetry: {json.dumps(extra)}"

    payload = {
        "model": model,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    timeout = Timeout(6.0, connect=3.0)
    limits = Limits(max_keepalive_connections=5, max_connections=10)

    try:
        async with AsyncClient(timeout=timeout, limits=limits) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.warning(
                    "LLM API returned status %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return None

            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed = json.loads(_clean_json_string(raw_content))

            raw_type = str(parsed.get("type", "")).lower()
            raw_severity = str(parsed.get("severity", "")).lower()
            raw_confidence = float(parsed.get("confidence", 0.75))
            raw_reasoning = str(parsed.get("reasoning", "LLM triage"))

            # Validate against domain contract enums
            incident_type = IncidentType(raw_type)
            incident_severity = IncidentSeverity(raw_severity)
            priority = SEVERITY_PRIORITY_MAP[incident_severity]
            confidence = max(0.0, min(1.0, raw_confidence))

            return TriageResult(
                type=incident_type,
                severity=incident_severity,
                priority=priority,
                confidence=confidence,
                reasoning=raw_reasoning[:120],
                classified_by="llm",
            )
    except Exception as exc:
        logger.warning("LLM triage failed or timed out: %s. Falling back to rules.", exc)
        return None


async def triage(
    text: str,
    source: str,
    extra: Optional[dict[str, Any]] = None,
) -> TriageResult:
    """
    Main triage entry point:
    1. Check in-memory LRU cache.
    2. Attempt LLM classification if API key is configured.
    3. Fall back to deterministic rule-based triage on failure or absent key.
    4. Cache and return result.
    """
    cache_key = f"{source}:{text.strip().lower()}"
    if extra:
        try:
            cache_key += f":{json.dumps(extra, sort_keys=True)}"
        except Exception:
            pass

    # Check cache
    if cache_key in _triage_cache:
        # Move to end for LRU
        result = _triage_cache[cache_key]
        _triage_cache.move_to_end(cache_key)
        return result

    # 1. Try LLM path
    result = await _llm_triage(text, source, extra)

    # 2. Fall back to rules if LLM not configured or failed
    if result is None:
        result = rules_triage(text, source, extra)

    # 3. Store in LRU cache
    if len(_triage_cache) >= CACHE_MAX_SIZE:
        _triage_cache.popitem(last=False)
    _triage_cache[cache_key] = result

    return result
