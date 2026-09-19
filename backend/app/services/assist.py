import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from bson import ObjectId
import httpx

from backend.app.config import settings

logger = logging.getLogger("resqai.assist")


def _rule_based_assistance(incident: Dict[str, Any]) -> Dict[str, Any]:
    inc_type = str(incident.get("type", "other")).lower()
    severity = str(incident.get("severity", "medium")).lower()

    reports = incident.get("reports", [])
    report_texts = [r.get("text") or r.get("normalized_text", "") for r in reports if r]
    combined_desc = " ".join(report_texts) if report_texts else incident.get("description", "Emergency incident reported.")

    summary = f"Emergency {inc_type.replace('_', ' ')} incident ({severity} severity) reported at {incident.get('address', 'incident location')}. {combined_desc[:120]}."

    if inc_type == "fire":
        assessment = f"High thermal threat and smoke risk. Potential structural spread at {incident.get('address')}."
        recommended_actions = [
            "Evacuate immediate 200m radius surrounding the structure",
            "Request local utility company to disconnect electrical grid",
            "Dispatch additional water tanker units to secure water supply",
            "Establish perimeter control and clear emergency access lanes",
            "Pre-alert nearest hospital burn unit for potential casualties"
        ]
        field_guidance = [
            "Wear full SCBA gear before entering smoke-filled structures",
            "Maintain continuous radio communication with command post",
            "Verify structural integrity before conducting interior search",
            "Establish rapid intervention team on standby"
        ]
    elif inc_type == "flood":
        assessment = f"Water surge threat level {severity.upper()}. Submerged access routes and potential trapped victims."
        recommended_actions = [
            "Evacuate residents from low-lying areas to high ground",
            "Deploy swift-water rescue teams and inflatable boats",
            "Issue public warning to avoid driving through flooded roads",
            "Coordinate with relief camp to prepare food and shelter",
            "Monitor water level gauges upstream"
        ]
        field_guidance = [
            "Always wear personal flotation devices near water",
            "Check for submerged power lines before wading",
            "Maintain tether lines during swift-water rescue operations",
            "Use sound signals in low-visibility conditions"
        ]
    elif inc_type == "road_accident":
        assessment = f"Traffic crash on roadway. Vehicle damage and potential trapped passengers or injuries."
        recommended_actions = [
            "Dispatch ambulance and hydraulic extrication equipment",
            "Set up traffic diversion and flare barrier 100m back",
            "Triage injured victims and coordinate transport priority",
            "Clear vehicle debris to restore traffic flow",
            "Document vehicle registration and scene evidence"
        ]
        field_guidance = [
            "Wear high-visibility reflective vests on roadway",
            "Stabilize crash vehicles before attempting extrication",
            "Disconnect vehicle battery to prevent fire ignition",
            "Maintain spinal immobilization for injured occupants"
        ]
    elif inc_type == "industrial_hazard" or inc_type == "gas_leak":
        assessment = f"Hazmat threat level {severity.upper()}. Hazardous gas/chemical spill risk in industrial zone."
        recommended_actions = [
            "Check wind direction and establish 500m upwind exclusion zone",
            "Evacuate downwind populated areas immediately",
            "Dispatch specialized hazmat response team",
            "Identify chemical substance UN number and SDS sheet",
            "Notify environmental protection authority"
        ]
        field_guidance = [
            "Approach scene strictly from UPWIND direction",
            "Wear Level A/B encapsulated chemical protective suit",
            "Do not use non-sparking electronic devices near gas",
            "Establish decontamination corridor before exiting zone"
        ]
    else:
        assessment = f"General emergency situation requiring immediate command coordination."
        recommended_actions = [
            "Dispatch primary responder units to scene coordinates",
            "Establish incident command post at safe distance",
            "Conduct preliminary damage and casualty assessment",
            "Maintain communications with central dispatch",
            "Log all operational events in chronological timeline"
        ]
        field_guidance = [
            "Exercise dynamic risk assessment upon arrival",
            "Maintain buddy system at all times",
            "Report any escalation immediately to command post",
            "Keep emergency access routes clear"
        ]

    return {
        "summary": summary,
        "assessment": assessment,
        "recommended_actions": recommended_actions[:5],
        "field_guidance": field_guidance[:4],
        "generated_by": "rules",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


async def generate_incident_assistance(
    db: Any,
    incident: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate AI incident assistance summary & recommendations with rule-based fallback."""
    inc_id = incident.get("_id")
    api_key = settings.effective_ai_key

    result = None

    if api_key and settings.ENABLE_AI_ANALYSIS:
        try:
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
                "You are an Emergency Command AI Assistant.\n"
                "Analyze the incident case file and output strict JSON:\n"
                "{\n"
                "  \"summary\": \"2-3 sentence situation summary\",\n"
                "  \"assessment\": \"threat level, affected area, and immediate risks\",\n"
                "  \"recommended_actions\": [\"up to 5 concrete control room actions\"],\n"
                "  \"field_guidance\": [\"up to 4 tactical safety notes for field teams\"]\n"
                "}\n"
                "Return raw JSON only."
            )

            reports_text = "\n".join([f"- [{r.get('source')}] {r.get('text')}" for r in incident.get("reports", []) if r])
            user_content = (
                f"Incident Type: {incident.get('type')}\n"
                f"Severity: {incident.get('severity')}\n"
                f"Address: {incident.get('address')}\n"
                f"Reports:\n{reports_text}\n"
                f"Assigned Resources: {incident.get('assigned_resources', [])}"
            )

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
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }

            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    if content.startswith("```"):
                        lines = content.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        content = "\n".join(lines).strip()

                    parsed = json.loads(content)
                    result = {
                        "summary": str(parsed.get("summary", "")),
                        "assessment": str(parsed.get("assessment", "")),
                        "recommended_actions": parsed.get("recommended_actions", [])[:5],
                        "field_guidance": parsed.get("field_guidance", [])[:4],
                        "generated_by": "llm",
                        "generated_at": datetime.now(timezone.utc).isoformat()
                    }
        except Exception as err:
            logger.warning(f"LLM assistance generation error: {err}")
            result = None

    if not result:
        result = _rule_based_assistance(incident)

    # Save to incident embedded field "ai_assist"
    await db.incidents.update_one(
        {"_id": inc_id},
        {"$set": {"ai_assist": result}}
    )

    return result


async def get_overall_briefing(db: Any) -> Dict[str, Any]:
    """Generate overall emergency situation briefing using MongoDB aggregations."""
    # 1. Group by severity
    sev_pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    sev_cursor = db.incidents.aggregate(sev_pipeline)
    sev_docs = await sev_cursor.to_list(length=10)
    sev_counts = {str(d["_id"]).lower(): d["count"] for d in sev_docs if d["_id"]}

    # 2. Top 3 priority incidents
    top_incidents_cursor = db.incidents.find(
        {"status": {"$nin": ["resolved", "closed", "RESOLVED", "CLOSED"]}}
    ).sort([("priority", 1), ("created_at", -1)]).limit(3)
    top_incidents_raw = await top_incidents_cursor.to_list(length=3)

    top_incidents = []
    for inc in top_incidents_raw:
        top_incidents.append({
            "incident_id": inc.get("incident_id") or str(inc.get("_id")),
            "title": inc.get("title", "Emergency Incident"),
            "type": inc.get("type"),
            "severity": inc.get("severity"),
            "priority": inc.get("priority"),
            "status": inc.get("status"),
            "address": inc.get("address")
        })

    # 3. Available resources count
    avail_resources_count = await db.resources.count_documents({"status": {"$in": ["available", "AVAILABLE"]}})
    total_active_incidents = sum(sev_counts.values())

    critical_count = sev_counts.get("critical", 0)
    high_count = sev_counts.get("high", 0)

    narrative = (
        f"Operational Briefing: {total_active_incidents} active incidents currently monitored. "
        f"Critical: {critical_count}, High: {high_count}. "
        f"{avail_resources_count} fleet units ready for deployment."
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_active_incidents": total_active_incidents,
        "severity_counts": {
            "critical": critical_count,
            "high": high_count,
            "medium": sev_counts.get("medium", 0),
            "low": sev_counts.get("low", 0)
        },
        "available_resources": avail_resources_count,
        "top_priority_incidents": top_incidents,
        "briefing_narrative": narrative
    }
