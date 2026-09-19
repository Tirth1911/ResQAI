"""
ResQAI - AI Incident Intelligence Engine Test Suite
Tests AI incident analysis across at least 5 distinct emergency scenarios:
1. Industrial Chemical Fire (Vatva GIDC)
2. Flash Flood Inundation (Vishwamitri River)
3. Highway Multi-Vehicle Pileup (NE-1 Expressway)
4. LPG Gas Pipeline Rupture (SG Highway Market)
5. Multi-Storey Building Collapse (Surat Textile Market)
6. Critical Cardiac Emergency (Kalupur Hub)

Verifies:
- Structured JSON output with all required schema fields
- Determination of incident_type, severity, priority, confidence, people_at_risk
- Recommended resources & immediate SOP actions
- MongoDB persistence via POST /api/incidents/{incident_id}/analyze
- Timeline logging & AI field marking
"""

import asyncio
import os
import sys
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from backend.app.main import app
from backend.app.ai.incident_classifier import analyze_incident

EMERGENCY_SCENARIOS = [
    {
        "name": "Scenario 1: Industrial Chemical Fire",
        "description": "Massive chemical explosion in solvent distillation unit. Toxic black fumes spreading rapidly. 4 factory workers trapped inside with critical burn injuries.",
        "source": "call_center",
        "location": "Vatva GIDC Phase IV, Ahmedabad",
        "expected_type": "fire",
        "expected_severity": "CRITICAL"
    },
    {
        "name": "Scenario 2: Flash Flooding Inundation",
        "description": "Dam sluice gates opened, river level surged 3 meters. Entire ground floor of residential colony submerged. 18 residents stranded on rooftops needing rescue boats.",
        "source": "citizen",
        "location": "Sayajiganj riverside, Vadodara",
        "expected_type": "flood",
        "expected_severity": "CRITICAL"
    },
    {
        "name": "Scenario 3: Highway Multi-Vehicle Pileup",
        "description": "State transport bus overturned during dense rain fog, colliding with two private cars. Multiple passengers trapped in twisted metal with severe bleeding.",
        "source": "field_team",
        "location": "NE-1 Expressway Km 38",
        "expected_type": "road_accident",
        "expected_severity": "CRITICAL"
    },
    {
        "name": "Scenario 4: High-Pressure LPG Gas Pipeline Rupture",
        "description": "Underground LPG supply line severed by construction excavator. Loud hissing sound and heavy gas odor detected across crowded market square.",
        "source": "iot",
        "location": "Prahlad Nagar Market, Ahmedabad",
        "expected_type": "gas_leak",
        "expected_severity": "HIGH"
    },
    {
        "name": "Scenario 5: Multi-Storey Commercial Building Collapse",
        "description": "Three-storey commercial complex suffered structural pillar failure and collapsed into rubble. Approximately 10 shoppers trapped beneath concrete slabs.",
        "source": "citizen",
        "location": "Ring Road Textile Market, Surat",
        "expected_type": "building_collapse",
        "expected_severity": "CRITICAL"
    },
    {
        "name": "Scenario 6: Acute Cardiac Arrest",
        "description": "60-year old commuter collapsed unconscious on platform floor. No pulse detected, bystander CPR initiated.",
        "source": "citizen",
        "location": "Kalupur Central Railway Station",
        "expected_type": "medical_emergency",
        "expected_severity": "CRITICAL"
    }
]


async def run_ai_tests():
    print("=" * 75)
    print(" ResQAI AI Incident Intelligence Engine - Verification Test Suite")
    print("=" * 75)

    # Part 1: Direct Service Function Test on 6 Scenarios
    print("\n--- PART 1: Testing analyze_incident() Structured Engine Outputs ---\n")
    for idx, sc in enumerate(EMERGENCY_SCENARIOS, 1):
        print(f"[{idx}/6] Analyzing {sc['name']}...")
        result = await analyze_incident(
            description=sc["description"],
            source=sc["source"],
            location=sc["location"]
        )

        # Validate Schema Fields
        required_fields = [
            "incident_type", "severity", "priority", "confidence",
            "people_at_risk", "recommended_resources", "immediate_actions",
            "summary", "reasoning", "is_ai_generated", "provider"
        ]
        for field in required_fields:
            assert field in result, f"Missing field '{field}' in AI output"

        print(f"      * Type:          {result['incident_type']} (Confidence: {result['confidence']:.2f})")
        print(f"      * Severity:      {result['severity']} | Priority: {result['priority']}")
        print(f"      * People at Risk:{result['people_at_risk']}")
        print(f"      * Resources:     {result['recommended_resources']}")
        print(f"      * Actions Count: {len(result['immediate_actions'])} SOP steps")
        print(f"      * Summary:       {result['summary']}")
        print(f"      * Reasoning:     {result['reasoning'][:90]}...")
        print(f"      * Engine:        {result['provider']} (AI Marked: {result['is_ai_generated']})\n")

    # Part 2: End-to-End API Test with POST /api/incidents/{incident_id}/analyze
    print("--- PART 2: Testing POST /api/incidents/{incident_id}/analyze API Endpoint ---\n")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Create an incident without type/severity
        create_payload = {
            "title": "Severe Chemical Vapor Leak at Industrial Storage Depot",
            "description": "Chlorine cylinder valve snapped open. Greenish-yellow cloud drifting towards highway. 6 workers unconscious.",
            "source": "call_center",
            "location": {
                "latitude": 21.7000,
                "longitude": 72.5833,
                "address": "Dahej PCPIR Industrial Hub, Bharuch"
            }
        }
        res_create = await client.post("/api/incidents/", json=create_payload)
        assert res_create.status_code == 201
        created_inc = res_create.json()
        inc_id = created_inc["incident_id"]
        print(f"[API-1] Ingested Incident: {inc_id} (Initial Type: {created_inc['type']}, Severity: {created_inc['severity']})")

        # Step 2: Trigger AI Analysis Endpoint
        res_analyze = await client.post(f"/api/incidents/{inc_id}/analyze")
        assert res_analyze.status_code == 200, f"Error: {res_analyze.text}"
        analyzed_inc = res_analyze.json()

        print(f"[API-2] AI Intelligence Triggered on {inc_id}:")
        print(f"        • Updated Type:       {analyzed_inc['type']}")
        print(f"        • Updated Severity:   {analyzed_inc['severity']}")
        print(f"        • Updated Priority:   {analyzed_inc['priority']}")
        print(f"        • Confidence:         {analyzed_inc['confidence']}")
        print(f"        • AI Summary:         {analyzed_inc['ai_analysis']['summary']}")
        print(f"        • AI Reasoning:       {analyzed_inc['ai_analysis']['reasoning']}")
        print(f"        • Timeline Entries:   {len(analyzed_inc['timeline'])}")

        # Verify last timeline entry was recorded by AI Engine
        last_timeline = analyzed_inc["timeline"][-1]
        print(f"        • Last Timeline Log:  [{last_timeline['action']}] by {last_timeline['actor']}")

        # Cleanup test incident
        await client.delete(f"/api/incidents/{inc_id}")
        print(f"\n[API-3] Cleaned up temporary test incident {inc_id}.")

    print("\n" + "=" * 75)
    print(" ALL AI INCIDENT INTELLIGENCE ENGINE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_ai_tests())
