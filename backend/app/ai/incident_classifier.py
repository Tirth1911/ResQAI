import os
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import httpx
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.models.incident import (
    IncidentType,
    IncidentSeverity,
    IncidentPriority,
    IncidentStatus,
)

logger = logging.getLogger("resqai.ai.classifier")


# =============================================================================
# 1. STRUCTURED OUTPUT SCHEMA
# =============================================================================

class AIAnalysisResult(BaseModel):
    incident_type: str = Field(..., description="Classified incident category: fire, flood, road_accident, medical_emergency, industrial_hazard, building_collapse, gas_leak, earthquake, other")
    severity: str = Field(..., description="Severity level: LOW, MEDIUM, HIGH, CRITICAL")
    priority: str = Field(..., description="Response priority: P1, P2, P3, P4")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    people_at_risk: int = Field(default=0, ge=0, description="Estimated number of individuals currently at risk")
    recommended_resources: List[str] = Field(default_factory=list, description="Recommended response units to dispatch")
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate Standard Operating Procedure (SOP) action items")
    summary: str = Field(..., description="Concise executive situational summary")
    reasoning: str = Field(..., description="Chain-of-thought explanation for why this severity/priority was assigned")
    is_ai_generated: bool = Field(default=True, description="Flag explicitly marking output as AI-derived")
    provider: str = Field(default="deterministic_rules", description="Underlying intelligence engine/model used")
    analyzed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =============================================================================
# 2. PROVIDER ABSTRACTION
# =============================================================================

class BaseAIProvider(ABC):
    """Abstract AI Provider for Incident Intelligence."""

    @abstractmethod
    async def analyze(self, description: str, source: str = "citizen", location_info: Optional[str] = None) -> AIAnalysisResult:
        pass


class DeterministicRuleBasedProvider(BaseAIProvider):
    """
    Deterministic rule-based & keyword classifier.
    Guarantees fast, 100% offline, reliable structured triage without external API dependencies.
    """

    SUPPORTED_TYPES = [
        "fire",
        "flood",
        "road_accident",
        "medical_emergency",
        "industrial_hazard",
        "building_collapse",
        "gas_leak",
        "earthquake",
        "other",
    ]

    async def analyze(self, description: str, source: str = "citizen", location_info: Optional[str] = None) -> AIAnalysisResult:
        text = description.lower()

        # 1. Type Classification
        incident_type = "other"
        type_confidence = 0.88

        if any(w in text for w in ["fire", "blaze", "smoke", "flames", "burning", "combustion", "arson", "forest fire"]):
            incident_type = "fire"
            type_confidence = 0.96
        elif any(w in text for w in ["flood", "water level", "submerged", "drowning", "river overflow", "inundation", "waterlogged"]):
            incident_type = "flood"
            type_confidence = 0.94
        elif any(w in text for w in ["crash", "accident", "collision", "overturned", "highway", "pileup", "vehicle", "traffic collision", "hit and run"]):
            incident_type = "road_accident"
            type_confidence = 0.95
        elif any(w in text for w in ["cardiac", "stroke", "heart attack", "unconscious", "bleeding", "patient", "medical", "respiratory", "cpr"]):
            incident_type = "medical_emergency"
            type_confidence = 0.93
        elif any(w in text for w in ["chemical", "toxic", "factory spill", "radiation", "acid leak", "refinery explosion", "industrial"]):
            incident_type = "industrial_hazard"
            type_confidence = 0.92
        elif any(w in text for w in ["collapse", "rubble", "debris", "trapped under", "structural failure", "roof fell", "slab collapse"]):
            incident_type = "building_collapse"
            type_confidence = 0.95
        elif any(w in text for w in ["gas leak", "lpg", "smell gas", "pipeline leak", "methane", "propane", "cylinder burst"]):
            incident_type = "gas_leak"
            type_confidence = 0.94
        elif any(w in text for w in ["earthquake", "tremor", "aftershock", "seismic", "richter"]):
            incident_type = "earthquake"
            type_confidence = 0.97

        # 2. Extract People at Risk via Regex
        people_at_risk = 0
        risk_patterns = [
            r"(\d+)\s*(?:people|persons|passengers|workers|citizens|residents|children|victims|casualties|trapped|injured|dead)",
            r"trapped\s*(?:about|around)?\s*(\d+)",
            r"(\d+)\s*trapped"
        ]
        for pat in risk_patterns:
            match = re.search(pat, text)
            if match:
                try:
                    people_at_risk = max(people_at_risk, int(match.group(1)))
                except Exception:
                    pass

        if people_at_risk == 0 and any(w in text for w in ["multiple", "several", "many", "crowd"]):
            people_at_risk = 5
        elif people_at_risk == 0 and any(w in text for w in ["mass casualty", "bus full", "building packed", "hundreds"]):
            people_at_risk = 25

        # 3. Severity & Priority Scoring
        is_critical = any(w in text for w in [
            "critical", "fatal", "mass casualty", "explosion", "several dead", "multiple trapped",
            "unconscious", "catastrophic", "extreme", "heart attack", "cardiac arrest", "massive"
        ]) or people_at_risk >= 5

        is_high = any(w in text for w in [
            "major", "severe", "spreading", "heavy", "serious injury", "head injury",
            "blaze", "submerged", "pipeline rupture", "flames visible", "rapidly", "toxic", "trapped"
        ]) or people_at_risk >= 2

        is_low = any(w in text for w in [
            "minor", "small", "contained", "no injuries", "controlled", "fender bender", "isolated"
        ]) and people_at_risk == 0

        if is_critical:
            severity = "CRITICAL"
            priority = "P1"
            reasoning = f"Categorized as CRITICAL/P1 due to life safety threat, high casualty potential ({people_at_risk} at risk), or rapid escalation factors."
        elif is_high:
            severity = "HIGH"
            priority = "P2"
            reasoning = f"Categorized as HIGH/P2 due to serious active hazard, property threat, or multiple involved individuals ({people_at_risk} at risk)."
        elif is_low:
            severity = "LOW"
            priority = "P4"
            reasoning = "Categorized as LOW/P4 as situation is small-scale, contained, with no immediate life danger."
        else:
            severity = "MEDIUM"
            priority = "P3"
            reasoning = f"Categorized as MEDIUM/P3 standard emergency requiring prompt multi-agency dispatch and verification."

        # 4. Recommended Resources & SOP Actions
        recommended_resources = []
        immediate_actions = []

        if incident_type == "fire":
            recommended_resources = ["FIRE_TRUCK", "AMBULANCE", "POLICE"]
            immediate_actions = [
                "Deploy primary Fire Tender and Water Bowser units immediately.",
                "Establish a 500-meter safety perimeter and clear evacuation route.",
                "Alert nearest Burn Unit / Trauma Center for standby casualties."
            ]
        elif incident_type == "flood":
            recommended_resources = ["RESCUE_TEAM", "DISASTER_TEAM", "AMBULANCE"]
            immediate_actions = [
                "Deploy motorized inflatable rescue boats and life jackets.",
                "Issue automated evacuation advisory to downstream residents.",
                "Coordinate with NDRF / SDRF water rescue teams."
            ]
        elif incident_type == "road_accident":
            recommended_resources = ["AMBULANCE", "POLICE", "FIRE_TRUCK"]
            immediate_actions = [
                "Dispatch Advanced Life Support (ALS) Ambulance and Traffic Squad.",
                "Deploy hydraulic jaws-of-life rescue gear if extrication is required.",
                "Notify nearest emergency trauma center for triage reception."
            ]
        elif incident_type == "medical_emergency":
            recommended_resources = ["AMBULANCE", "MEDICAL_TEAM"]
            immediate_actions = [
                "Dispatch nearest ALS unit equipped with AED, defibrillator, and oxygen.",
                "Provide live dispatch CPR/first-aid instructions to caller.",
                "Request hospital green corridor if critical transit is needed."
            ]
        elif incident_type == "gas_leak":
            recommended_resources = ["DISASTER_TEAM", "FIRE_TRUCK", "POLICE"]
            immediate_actions = [
                "Deploy Hazmat detection crew with self-contained breathing gear.",
                "Isolate electrical grid and prohibit ignition sources within 300m.",
                "Establish upwind staging command post."
            ]
        elif incident_type == "industrial_hazard":
            recommended_resources = ["DISASTER_TEAM", "FIRE_TRUCK", "AMBULANCE"]
            immediate_actions = [
                "Deploy chemical foam neutralization unit and vapor suppression.",
                "Activate GIDC / Industrial Zone emergency containment protocol.",
                "Coordinate medical antidotes and toxic exposure decontamination."
            ]
        elif incident_type == "building_collapse":
            recommended_resources = ["RESCUE_TEAM", "DISASTER_TEAM", "AMBULANCE", "FIRE_TRUCK"]
            immediate_actions = [
                "Dispatch Urban Search & Rescue (USAR) canine and acoustic listening teams.",
                "Mobilize heavy crane and pneumatic lifting bag equipment.",
                "Establish on-site field resuscitation triage area."
            ]
        elif incident_type == "earthquake":
            recommended_resources = ["DISASTER_TEAM", "RESCUE_TEAM", "MEDICAL_TEAM"]
            immediate_actions = [
                "Deploy multi-agency structural integrity assessment strike teams.",
                "Issue regional aftershock safety advisory.",
                "Open designated community relief shelters."
            ]
        else:
            recommended_resources = ["POLICE", "AMBULANCE"]
            immediate_actions = [
                "Dispatch rapid response unit for ground assessment.",
                "Maintain continuous communication with reporting party."
            ]

        # 5. Executive Summary
        location_str = f" at {location_info}" if location_info else ""
        summary = (
            f"AI Assessment: {severity} severity {incident_type.replace('_', ' ').title()} reported via {source}{location_str}. "
            f"Estimated {people_at_risk} person(s) at risk. Dispatched priority {priority}."
        )

        return AIAnalysisResult(
            incident_type=incident_type,
            severity=severity,
            priority=priority,
            confidence=type_confidence,
            people_at_risk=people_at_risk,
            recommended_resources=recommended_resources,
            immediate_actions=immediate_actions,
            summary=summary,
            reasoning=reasoning,
            is_ai_generated=True,
            provider="deterministic_rule_engine",
            analyzed_at=datetime.now(timezone.utc).isoformat()
        )


class OpenAICompatibleProvider(BaseAIProvider):
    """
    LLM Provider supporting OpenAI API, Groq, Ollama, vLLM, and any OpenAI-compatible API.
    Uses structured prompt & JSON mode. Falls back to deterministic rules if unavailable.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.fallback = DeterministicRuleBasedProvider()

    async def analyze(self, description: str, source: str = "citizen", location_info: Optional[str] = None) -> AIAnalysisResult:
        system_prompt = (
            "You are ResQAI, an expert emergency response and triage intelligence AI. "
            "Analyze the given distress report and output STRICT valid JSON with the exact following schema:\n"
            "{\n"
            '  "incident_type": "fire|flood|road_accident|medical_emergency|industrial_hazard|building_collapse|gas_leak|earthquake|other",\n'
            '  "severity": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "priority": "P1|P2|P3|P4",\n'
            '  "confidence": <float between 0.0 and 1.0>,\n'
            '  "people_at_risk": <integer count>,\n'
            '  "recommended_resources": ["AMBULANCE", "FIRE_TRUCK", "POLICE", "RESCUE_TEAM", "MEDICAL_TEAM", "DISASTER_TEAM"],\n'
            '  "immediate_actions": ["<SOP Action 1>", "<SOP Action 2>"],\n'
            '  "summary": "<2 sentence situational summary>",\n'
            '  "reasoning": "<explanation for severity and priority ranking>"\n'
            "}\n"
            "CRITICAL: Never invent facts. Base conclusions strictly on provided emergency details."
        )

        user_content = f"Source: {source}\nLocation: {location_info or 'Unknown'}\nDescription: {description}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                # Validate with Pydantic
                result = AIAnalysisResult(
                    incident_type=parsed.get("incident_type", "other"),
                    severity=parsed.get("severity", "MEDIUM"),
                    priority=parsed.get("priority", "P3"),
                    confidence=float(parsed.get("confidence", 0.95)),
                    people_at_risk=int(parsed.get("people_at_risk", 0)),
                    recommended_resources=parsed.get("recommended_resources", ["POLICE"]),
                    immediate_actions=parsed.get("immediate_actions", ["Dispatch assessment team"]),
                    summary=parsed.get("summary", description[:150]),
                    reasoning=parsed.get("reasoning", "Assessed by LLM intelligence."),
                    is_ai_generated=True,
                    provider=f"llm:{self.model}",
                    analyzed_at=datetime.now(timezone.utc).isoformat()
                )
                return result
            else:
                logger.warning(f"LLM API returned status {response.status_code}. Falling back to deterministic classifier.")
                return await self.fallback.analyze(description, source, location_info)
        except Exception as e:
            logger.warning(f"Error calling LLM provider: {e}. Falling back to deterministic classifier.")
            return await self.fallback.analyze(description, source, location_info)


# =============================================================================
# 3. AI ENGINE FACTORY & SERVICE FUNCTIONS
# =============================================================================

def get_ai_provider() -> BaseAIProvider:
    """Factory returning configured AI Provider or fallback deterministic engine."""
    api_key = settings.effective_ai_key
    if api_key and settings.LLM_PROVIDER != "mock":
        return OpenAICompatibleProvider(
            api_key=api_key,
            model=settings.AI_MODEL,
            base_url=settings.AI_BASE_URL
        )
    return DeterministicRuleBasedProvider()


async def analyze_incident(
    description: str,
    source: str = "citizen",
    location: Optional[Union[Dict[str, Any], str]] = None
) -> Dict[str, Any]:
    """
    Analyze incident description and return structured JSON dictionary.
    Safe and robust: falls back to deterministic rule classifier if AI API key is omitted.
    """
    location_str = None
    if isinstance(location, dict):
        location_str = location.get("address") or f"Coords: {location.get('coordinates', [])}"
    elif isinstance(location, str):
        location_str = location

    provider = get_ai_provider()
    result = await provider.analyze(
        description=description,
        source=source,
        location_info=location_str
    )
    return result.model_dump()


async def analyze_and_update_incident_in_db(db, incident_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch incident by incident_id from MongoDB, run AI Incident Intelligence Engine,
    and persist updated ai_analysis, severity, priority, type, confidence, and timeline.
    """
    from backend.app.services.db_service import DBService, clean_mongo_doc
    from backend.app.websocket.manager import ws_manager
    from bson import ObjectId

    incident = await DBService.get_incident(db, incident_id)
    if not incident:
        return None

    desc = incident.get("description", "")
    title = incident.get("title", "")
    full_text = f"{title}. {desc}"
    source = incident.get("source", "citizen")
    address = incident.get("address")

    analysis_data = await analyze_incident(
        description=full_text,
        source=source,
        location=address
    )

    now_utc = datetime.now(timezone.utc)
    update_doc = {
        "type": analysis_data["incident_type"],
        "severity": analysis_data["severity"],
        "priority": analysis_data["priority"],
        "confidence": analysis_data["confidence"],
        "ai_analysis": analysis_data,
        "updated_at": now_utc
    }

    timeline_entry = {
        "timestamp": now_utc,
        "action": "AI Analysis Completed",
        "actor": f"AI Engine ({analysis_data.get('provider', 'ResQAI-AI')})",
        "details": f"Classified as {analysis_data['incident_type']} | Severity: {analysis_data['severity']} | Priority: {analysis_data['priority']} | Confidence: {analysis_data['confidence']:.2f}"
    }

    query = {"incident_id": incident_id}
    if ObjectId.is_valid(incident_id):
        query = {"$or": [{"incident_id": incident_id}, {"_id": ObjectId(incident_id)}]}

    await db.incidents.update_one(
        query,
        {
            "$set": update_doc,
            "$push": {"timeline": timeline_entry}
        }
    )

    updated_incident = await db.incidents.find_one(query)
    cleaned = clean_mongo_doc(updated_incident)

    if cleaned:
        from backend.app.websocket.manager import WebSocketEventType
        await ws_manager.broadcast_event(
            WebSocketEventType.INCIDENT_CLASSIFIED,
            cleaned
        )
        if str(cleaned.get("severity", "")).upper() == "CRITICAL" or str(cleaned.get("priority", "")).upper() == "P1":
            await ws_manager.broadcast_event(
                WebSocketEventType.INCIDENT_ESCALATED,
                cleaned
            )

    return cleaned
