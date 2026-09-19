from typing import List, Dict, Any, Optional
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

