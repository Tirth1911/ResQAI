import os
import json
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import httpx
from backend.app.config import settings

logger = logging.getLogger("resqai.triage")


class TriageResult(BaseModel):
    type: str
    severity: str
    priority: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    classified_by: str  # "llm" or "rules"


def map_severity_to_priority(severity: str) -> str:
    s = str(severity).lower()
    if s == "critical":
        return "P1"
    elif s == "high":
        return "P2"
    elif s == "medium":
        return "P3"
    else:
        return "P4"


_LRU_CACHE: Dict[str, TriageResult] = {}
_MAX_CACHE_SIZE = 1000


def _rules_triage(text: str, source: str, extra: Optional[Dict[str, Any]] = None) -> TriageResult:
    text_lower = (text or "").lower()
    extra_dict = extra or {}
    source_lower = str(source).lower()

    # 1. Type matching by keywords
    inc_type = "other"

    if any(k in text_lower for k in ["fire", "smoke", "burning", "blaze"]):
        inc_type = "fire"
    elif any(k in text_lower for k in ["flood", "water level", "submerged", "overflow"]):
        inc_type = "flood"
    elif any(k in text_lower for k in ["crash", "collision", "accident", "overturned", "traffic incident"]):
        inc_type = "road_accident"
    elif any(k in text_lower for k in ["heart", "unconscious", "bleeding", "injured", "chest pain", "cardiac", "medical", "er overflow"]):
        inc_type = "medical_emergency"
    elif any(k in text_lower for k in ["gas leak", "chemical", "explosion", "factory", "toxic", "industrial"]):
        if "gas" in text_lower and "leak" in text_lower:
            inc_type = "gas_leak"
        else:
            inc_type = "industrial_hazard"
    elif "collapse" in text_lower:
        inc_type = "building_collapse"
    elif "earthquake" in text_lower or "quake" in text_lower:
        inc_type = "earthquake"

    # 2. IoT Sensor Extra Thresholds
    if source_lower in ["iot_sensor", "iot", "sensor"]:
        sensor_type = str(extra_dict.get("sensor", "")).lower()
        val = extra_dict.get("value", 0)
        try:
            val_num = float(val)
        except (ValueError, TypeError):
            val_num = 0.0

        if sensor_type == "smoke" or "smoke" in text_lower or val_num > 100:
            inc_type = "fire"
            if val_num > 500:
                severity_init = "high"
            else:
                severity_init = "medium"

    # 3. Severity Determination & Boosters
    severity = "medium"

    critical_boosters = [
        "trapped", "explosion", "multiple", "children", "spreading",
        "casualties", "dead", "collapsed", "mass casualty", "mass-casualty"
    ]
    low_boosters = ["minor", "small", "no injuries", "contained"]

    # Hospital extra check
    if extra_dict.get("casualty_count", 0) >= 10 or extra_dict.get("casualties", 0) >= 10:
        severity = "critical"

    if any(k in text_lower for k in critical_boosters):
        severity = "critical"
    elif any(k in text_lower for k in ["severe", "heavy", "burning", "blaze", "major"]):
        if severity != "critical":
            severity = "high"

    if any(k in text_lower for k in low_boosters) and severity not in ["critical", "high"]:
        severity = "low"

    # If IoT smoke > 500, enforce at least high
    if source_lower in ["iot_sensor", "iot", "sensor"]:
        try:
            val_num = float(extra_dict.get("value", 0))
            if val_num > 500 and severity not in ["critical", "high"]:
                severity = "high"
        except (ValueError, TypeError):
            pass

    priority = map_severity_to_priority(severity)
    reasoning = f"Rule-based triage: matched keywords for type '{inc_type}' and severity '{severity}'."

    return TriageResult(
        type=inc_type,
        severity=severity,
        priority=priority,
        confidence=0.6,
        reasoning=reasoning[:150],
        classified_by="rules"
    )


async def _llm_triage(text: str, source: str, extra: Optional[Dict[str, Any]] = None) -> Optional[TriageResult]:
    api_key = settings.effective_ai_key
    if not api_key:
        return None

    provider = (os.getenv("LLM_PROVIDER") or settings.LLM_PROVIDER or "auto").lower()
    if provider == "openai" or ("sk-" in api_key and "gsk_" not in api_key):
        url = "https://api.openai.com/v1/chat/completions"
        model = settings.AI_MODEL or "gpt-4o-mini"
    else:
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile" if ("gsk_" in api_key or provider == "groq") else (settings.AI_MODEL or "llama3-8b-8192")

    if settings.AI_BASE_URL:
        url = f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions"

    system_prompt = (
        "You are an emergency command-center AI triage engine.\n"
        "Analyze emergency text reports and classify into strict JSON:\n"
        "Allowed types: [fire, flood, road_accident, medical_emergency, industrial_hazard, building_collapse, gas_leak, earthquake, other]\n"
        "Allowed severities:\n"
        "  - critical: immediate threat to multiple lives / explosion / mass casualty / spreading fire in populated area\n"
        "  - high: life threat or large damage\n"
        "  - medium: contained danger\n"
        "  - low: minor/no injury\n"
        "JSON format: {\"type\": \"fire\", \"severity\": \"critical\", \"confidence\": 0.95, \"reasoning\": \"<=25 words summary\"}\n"
        "Return ONLY raw valid JSON object without markdown formatting."
    )

    user_content = f"Source: {source}\nText: {text}\nExtra info: {json.dumps(extra or {})}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.warning(f"LLM API returned status {resp.status_code}: {resp.text}")
                return None

            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Clean markdown code fences if present
            if content.startswith("```"):
                lines = content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()

            parsed = json.loads(content)

            raw_type = str(parsed.get("type", "other")).lower()
            allowed_types = {
                "fire", "flood", "road_accident", "medical_emergency",
                "industrial_hazard", "building_collapse", "gas_leak", "earthquake", "other"
            }
            if raw_type not in allowed_types:
                if "crash" in raw_type or "accident" in raw_type:
                    raw_type = "road_accident"
                elif "medical" in raw_type:
                    raw_type = "medical_emergency"
                elif "gas" in raw_type:
                    raw_type = "gas_leak"
                elif "industrial" in raw_type:
                    raw_type = "industrial_hazard"
                else:
                    raw_type = "other"

            raw_severity = str(parsed.get("severity", "medium")).lower()
            allowed_severities = {"critical", "high", "medium", "low"}
            if raw_severity not in allowed_severities:
                raw_severity = "medium"

            confidence = float(parsed.get("confidence", 0.9))
            confidence = max(0.0, min(1.0, confidence))

            reasoning = str(parsed.get("reasoning", "LLM automated triage classification."))[:150]
            priority = map_severity_to_priority(raw_severity)

            return TriageResult(
                type=raw_type,
                severity=raw_severity,
                priority=priority,
                confidence=confidence,
                reasoning=reasoning,
                classified_by="llm"
            )
    except Exception as err:
        logger.warning(f"LLM triage call failed: {err}")
        return None


async def triage(text: str, source: str, extra: Optional[Dict[str, Any]] = None) -> TriageResult:
    """Classify report using LLM path with LRU cache & rule-based fallback."""
    cache_key = f"{str(source).lower()}:{text.strip().lower()}"
    if cache_key in _LRU_CACHE:
        return _LRU_CACHE[cache_key]

    # Step 1: LLM path
    res = await _llm_triage(text, source, extra)

    # Step 2: Rules fallback if LLM path returned None
    if not res:
        res = _rules_triage(text, source, extra)

    # Maintain LRU cache
    if len(_LRU_CACHE) >= _MAX_CACHE_SIZE:
        _LRU_CACHE.clear()

    _LRU_CACHE[cache_key] = res
    return res
