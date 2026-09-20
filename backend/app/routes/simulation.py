from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.database import get_database
from backend.app.services.simulation_service import (
    simulation_engine,
    SIMULATION_SCENARIOS,
)

router = APIRouter()


class StartSimulationRequest(BaseModel):
    scenario_id: Optional[str] = Field(None, description="Scenario ID (road_accident, building_fire, urban_flood, medical_emergency, gas_leak) or null to run first or all")
    speed_multiplier: float = Field(1.0, ge=0.25, le=10.0, description="Simulation playback speed factor (e.g. 1.0, 2.0, 5.0)")
    auto_play_all: bool = Field(False, description="Automatically cycle through all 5 scenarios in sequence")
    step_delay_seconds: float = Field(3.0, ge=1.0, le=30.0, description="Delay in seconds between pipeline stages")


@router.post("/start", summary="Start Emergency Simulation Sequence")
async def start_simulation(
    payload: Optional[StartSimulationRequest] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Start the ResQAI Emergency Simulation Engine.
    Executes realistic multi-step crisis scenarios with live AI triage,
    3-Signal NLP/Geo deduplication merging, resource dispatch, and WebSocket streaming.
    """
    req = payload or StartSimulationRequest()
    status_data = await simulation_engine.start(
        db=db,
        scenario_id=req.scenario_id,
        speed_multiplier=req.speed_multiplier,
        auto_play_all=req.auto_play_all,
        step_delay_seconds=req.step_delay_seconds
    )
    return {
        "status": "simulation_started",
        "simulation": status_data
    }


@router.post("/stop", summary="Stop Running Simulation")
async def stop_simulation():
    """Immediately halt the running simulation sequence."""
    status_data = await simulation_engine.stop()
    return {
        "status": "simulation_stopped",
        "simulation": status_data
    }


@router.post("/reset", summary="Reset Simulation State & Telemetry")
async def reset_simulation(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Reset simulation engine state, clear events log, and release simulated fleet resources."""
    status_data = await simulation_engine.reset(db)
    return {
        "status": "simulation_reset",
        "simulation": status_data
    }


@router.get("/status", summary="Get Current Simulation Telemetry & State")
async def get_simulation_status():
    """Fetch live status of the simulation engine including current stage, step progress, and event logs."""
    return simulation_engine.get_status()


@router.post("/trigger", summary="Trigger Single Scenario (Legacy/Direct Trigger)")
async def trigger_single_scenario(
    scenario_index: int = Query(0, ge=0, le=4, description="Scenario index (0 to 4)"),
    duplicate_simulation: bool = Query(True, description="Inject duplicate report for testing deduplication"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Trigger a single scenario immediately for quick one-click demonstrations."""
    scenario = SIMULATION_SCENARIOS[scenario_index % len(SIMULATION_SCENARIOS)]
    status_data = await simulation_engine.start(
        db=db,
        scenario_id=scenario["id"],
        speed_multiplier=1.5,
        auto_play_all=False,
        step_delay_seconds=2.5
    )
    return {
        "status": "scenario_triggered",
        "scenario_title": scenario["title"],
        "simulation": status_data
    }


@router.post("/demo/setup", summary="Setup Clean Demo Environment for Judge Demonstration")
async def setup_demo(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Cleans up past demo artifacts and seeds 3 ready fleet units for the 13-step judge walkthrough.
    Ensures repeatability with zero manual database cleanup needed.
    """
    return await simulation_engine.setup_demo_environment(db)


@router.post("/demo/step/{step_number}", summary="Execute Specific Demo Step (1 to 13)")
async def run_demo_step(
    step_number: int,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Executes a discrete step in the 13-step ResQAI Judge Demo Walkthrough:
    1: Overview & standby fleet
    2: Create critical road accident
    3: AI triage (CRITICAL, P1)
    4: AI situation summary & immediate actions
    5: Recommend nearest Ambulance, Police, Fire Rescue
    6: Dispatch multi-unit fleet
    7: Map updates
    8: Ingest 2nd citizen report
    9: 3-Signal Deduplication match
    10: Merge duplicate reports
    11: Broadcast tactical notification
    12: Resolve incident & release units
    13: Recompute executive analytics
    """
    if step_number < 1 or step_number > 13:
        return {"error": "Step number must be between 1 and 13", "step": step_number}
    return await simulation_engine.execute_demo_step(db, step_number)


_sim_counter = 0

SIMULATED_CRITICAL_SCENARIOS = [
    {
        "title": "Major Chemical Storage Tanker Fire",
        "type": "FIRE",
        "severity": "CRITICAL",
        "priority": "P1",
        "address": "Odhav GIDC Phase 3, Ahmedabad",
        "coordinates": [72.656, 23.031],
        "description": "Severe chemical storage tanker rupture and fire. Thick toxic vapor cloud spreading towards nearby factory sheds. Immediate multi-unit HAZMAT and fire tender dispatch required.",
        "reasoning": "Chemical vapor plume poses immediate inhalation toxicity hazard to nearby workers. Priority P1 dispatch recommended for Fire Engine and HAZMAT units."
    },
    {
        "title": "Multi-Vehicle Flyover Collision with Fuel Spillage",
        "type": "ROAD_ACCIDENT",
        "severity": "CRITICAL",
        "priority": "P1",
        "address": "SG Highway, Iscon Flyover, Ahmedabad",
        "coordinates": [72.507, 23.029],
        "description": "3-car pileup involving heavy container truck on flyover. Trapped passengers, active fuel leak on roadway blocking traffic.",
        "reasoning": "High-speed multi-lane collision with entrapment and flammability risk. Immediate ALS Ambulance and PCR Patrol dispatch required."
    },
    {
        "title": "Substation Transformer Explosion & Structural Blaze",
        "type": "FIRE",
        "severity": "CRITICAL",
        "priority": "P1",
        "address": "Naroda Industrial Estate, Ahmedabad",
        "coordinates": [72.655, 23.071],
        "description": "High-voltage transformer explosion causing structural fire in adjacent manufacturing plant. Multiple workers reported trapped on upper level.",
        "reasoning": "Electrical grid explosion with active structural collapse hazard. Water tender and heavy rescue team required immediately."
    },
    {
        "title": "Sabarmati Riverfront Flash Surge & Stranded Workers",
        "type": "FLOOD",
        "severity": "HIGH",
        "priority": "P2",
        "address": "Near Subhash Bridge Riverfront Bank, Ahmedabad",
        "coordinates": [72.585, 23.061],
        "description": "Heavy upstream water release caused sudden riverfront surge. 3 construction workers stranded on low-lying mud bank.",
        "reasoning": "Rising water level requires rapid boat deployment and NDRF water rescue team before dusk."
    }
]


@router.post("/simulate-critical", summary="Simulate New Critical Emergency Incident on Server")
@router.post("/simulate-incident", summary="Simulate New Emergency Incident on Server", include_in_schema=False)
async def simulate_critical_incident(
    scenario_idx: Optional[int] = Query(None, description="Optional scenario index (0 to 3)"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate an authentic emergency incident on the SERVER:
    1. Validate and process incident data
    2. Commit new record to MongoDB
    3. Determine required response resources & AI triage
    4. Save persistent notification in database
    5. Broadcast NEW_INCIDENT, DISPATCH_REQUIRED, and ALERT_CREATED via WebSocket
    6. Synchronize all connected dashboards in real time without page refresh
    """
    global _sim_counter
    if scenario_idx is not None:
        idx = scenario_idx % len(SIMULATED_CRITICAL_SCENARIOS)
    else:
        idx = _sim_counter % len(SIMULATED_CRITICAL_SCENARIOS)
        _sim_counter += 1

    template = SIMULATED_CRITICAL_SCENARIOS[idx]
    now_dt = datetime.now(timezone.utc)

    from backend.app.services.db_service import DBService
    from backend.app.services.resource_matcher import ResourceMatcher
    from backend.app.services.realtime import (
        broadcast_incident_created,
        broadcast_dispatch_required,
        broadcast_alert_created,
        broadcast_incident_escalated
    )

    doc_data = {
        "title": template["title"],
        "description": template["description"],
        "source": "HOTLINE",
        "type": template["type"],
        "severity": template["severity"],
        "priority": template["priority"],
        "status": "REPORTED",
        "address": template["address"],
        "location": {
            "type": "Point",
            "coordinates": template["coordinates"]
        },
        "reported_at": now_dt,
        "assigned_resources": [],
        "confidence": 0.96,
        "ai_analysis": {
            "summary": template["title"],
            "reasoning": template["reasoning"],
            "incident_type": template["type"],
            "severity": template["severity"],
            "priority": template["priority"],
            "priority_score": 95 if template["severity"] == "CRITICAL" else 75,
            "confidence": 0.96,
            "recommended_actions": [
                "Establish perimeter safety cordon",
                "Deploy nearest emergency units immediately",
                "Alert sector trauma centers"
            ]
        }
    }

    # 1. Commit to MongoDB
    created = await DBService.create_incident(db, doc_data)
    incident_id = created["incident_id"]

    # 2. Compute dispatch recommendations
    rec_ids = []
    try:
        rec_res = await ResourceMatcher.recommend_resources_for_incident(db, incident_id, limit=3)
        if rec_res and rec_res.recommendations:
            rec_ids = [r.resource_id for r in rec_res.recommendations]
    except Exception as e:
        rec_ids = ["RES-FIR-NAVRANG-01", "RES-HAZ-ODHAV-01", "RES-AMB-108-01"]

    # 3. Create persistent Notification in MongoDB
    alert_doc = {
        "notification_id": f"notif_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{incident_id}",
        "title": f"🚨 NEW CRITICAL INCIDENT: {created['title']}",
        "message": f"{created['title']} reported at {created['address']}. Priority: {created['priority']}",
        "severity": created["severity"],
        "incident_id": incident_id,
        "location": created["address"],
        "priority": created["priority"],
        "read": False,
        "created_at": now_dt
    }
    await db.notifications.insert_one(dict(alert_doc))

    # 4. Broadcast real-time WebSocket events in guaranteed sequence
    await broadcast_incident_created(created)
    await broadcast_dispatch_required(
        incident_id=incident_id,
        required_resource_type=created["type"],
        recommended_resource_ids=rec_ids,
        priority=created["priority"],
        location=created["address"],
        reason=template["reasoning"]
    )
    await broadcast_alert_created(alert_doc)
    if created["severity"] == "CRITICAL":
        await broadcast_incident_escalated(created)

    return {
        "status": "success",
        "message": "Critical incident simulated on server and broadcast via WebSocket.",
        "incident": created,
        "recommended_resource_ids": rec_ids
    }

