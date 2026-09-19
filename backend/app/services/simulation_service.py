import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.database import DatabaseManager
from backend.app.config import settings
from backend.app.models.incident import (
    IncidentType,
    IncidentSeverity,
    IncidentPriority,
    IncidentStatus,
    IncidentSource,
)
from backend.app.models.resource import ResourceStatus, ResourceCategory
from backend.app.services.db_service import DBService, clean_mongo_doc
from backend.app.services.duplicate_detector import DuplicateDetector
from backend.app.services.resource_matcher import ResourceMatcher
from backend.app.services.alert_service import AlertService
from backend.app.ai.incident_classifier import analyze_incident
from backend.app.websocket.manager import ws_manager, WebSocketEventType

logger = logging.getLogger("resqai.simulation_service")

SIMULATION_SCENARIOS = [
    {
        "id": "road_accident",
        "title": "Major Highway Collision & Pileup",
        "type": IncidentType.ROAD_ACCIDENT.value,
        "initial_severity": IncidentSeverity.HIGH.value,
        "initial_priority": IncidentPriority.P1.value,
        "address": "Outer Ring Road Junction, Bellandur, Bangalore",
        "coordinates": [77.6745, 12.9252],  # [lon, lat]
        "source": "citizen",
        "report_1": {
            "title": "Major multi-vehicle collision near Outer Ring Road",
            "description": "Passenger bus collided with two sedans during heavy traffic. Overturned vehicle, severe injuries, fuel leaking across 2 lanes.",
            "source": "citizen",
            "lat": 12.9252,
            "lon": 77.6745
        },
        "report_2_duplicate": {
            "title": "Severe road crash near Bellandur flyover",
            "description": "Flipped bus and crushed cars blocking Outer Ring Road. Multiple passengers trapped, urgent ambulances and fire truck needed.",
            "source": "citizen",
            "lat": 12.9258,
            "lon": 77.6751  # ~80m away
        },
        "ai_triage": {
            "incident_type": "road_accident",
            "severity": "CRITICAL",
            "priority": "P1",
            "confidence": 0.96,
            "situation_summary": "High-velocity multi-vehicle collision with overturned passenger bus and high risk of secondary vehicle fire from fuel leakage. Critical trauma extrication required.",
            "people_at_risk": 18,
            "immediate_actions": [
                "Dispatch Heavy Hydraulic Extrication Fire Truck",
                "Deploy Advanced Life Support (ALS) Trauma Ambulances",
                "Activate Traffic Police for 500m arterial road perimeter diversion",
                "Alert St. John's Level-1 Trauma Emergency Center"
            ],
            "recommended_resources": ["AMBULANCE", "FIRE_TRUCK", "POLICE"]
        }
    },
    {
        "id": "building_fire",
        "title": "Commercial High-Rise Structural Fire",
        "type": IncidentType.FIRE.value,
        "initial_severity": IncidentSeverity.CRITICAL.value,
        "initial_priority": IncidentPriority.P1.value,
        "address": "Tech Zone Tower B, Electronic City Phase 1, Bangalore",
        "coordinates": [77.5946, 12.9716],
        "source": "iot",
        "report_1": {
            "title": "High-Rise Commercial Building Fire - 5th Floor",
            "description": "Electrical short-circuit on 5th floor. Dense black smoke rising into upper office suites, HVAC ducts compromised, fire alarms triggered.",
            "source": "iot",
            "lat": 12.9716,
            "lon": 77.5946
        },
        "report_2_duplicate": {
            "title": "Thick smoke billowing from Tech Zone Tower B",
            "description": "Visible flames and heavy black smoke coming out of windows on 5th floor in Electronic City Phase 1. Over 50 people evacuating towards rooftop.",
            "source": "citizen",
            "lat": 12.9721,
            "lon": 77.5951  # ~75m away
        },
        "ai_triage": {
            "incident_type": "fire",
            "severity": "CRITICAL",
            "priority": "P1",
            "confidence": 0.98,
            "situation_summary": "Rapidly propagating structural commercial fire on 5th floor with vertical smoke funneling. High occupant density with rooftop evacuation underway.",
            "people_at_risk": 65,
            "immediate_actions": [
                "Dispatch 50-Meter Hydraulic Aerial Ladder Platform Fire Truck",
                "Deploy Thermal Drone Recon for structural heat signature mapping",
                "Dispatch Burn & Inhalation Specialized Ambulances",
                "Initiate emergency building HVAC power shutdown"
            ],
            "recommended_resources": ["FIRE_TRUCK", "AMBULANCE", "RESCUE_TEAM"]
        }
    },
    {
        "id": "urban_flood",
        "title": "Severe Flash Flood & Canal Breach",
        "type": IncidentType.FLOOD.value,
        "initial_severity": IncidentSeverity.HIGH.value,
        "initial_priority": IncidentPriority.P2.value,
        "address": "BTM Layout 2nd Stage Canal Sector, Bangalore",
        "coordinates": [77.6101, 12.9165],
        "source": "citizen",
        "report_1": {
            "title": "Stormwater Drain Overflow & Ground Floor Inundation",
            "description": "Cloudburst caused canal breach. Water levels reached 4.5 feet across residential streets, ground floor houses submerged, elderly stranded.",
            "source": "citizen",
            "lat": 12.9165,
            "lon": 77.6101
        },
        "report_2_duplicate": {
            "title": "Heavy flooding in BTM Layout Stage 2",
            "description": "Canal water entering all ground floor houses near BTM layout. Cars floating, families trapped inside, urgent motorized boats required.",
            "source": "citizen",
            "lat": 12.9159,
            "lon": 77.6108  # ~90m away
        },
        "ai_triage": {
            "incident_type": "flood",
            "severity": "HIGH",
            "priority": "P2",
            "confidence": 0.94,
            "situation_summary": "Urban stormwater canal breach resulting in rapid localized flooding up to 4.5 ft. Stranded vulnerable populations requiring waterborne evacuation.",
            "people_at_risk": 35,
            "immediate_actions": [
                "Deploy Inflatable Motorized Rescue Boats (NDRF Fleet)",
                "Dispatch High-Capacity Industrial Dewatering Pump Units",
                "Establish Temporary Relief & First-Aid Shelter at Community Hall",
                "De-energize local sub-station transformers to eliminate electrocution hazard"
            ],
            "recommended_resources": ["RESCUE_TEAM", "DISASTER_TEAM", "AMBULANCE"]
        }
    },
    {
        "id": "medical_emergency",
        "title": "Mass Heat Exhaustion & Cardiac Crisis",
        "type": IncidentType.MEDICAL_EMERGENCY.value,
        "initial_severity": IncidentSeverity.CRITICAL.value,
        "initial_priority": IncidentPriority.P1.value,
        "address": "Cubbon Park Pavilion Sports Complex, Bangalore",
        "coordinates": [77.5992, 12.9766],
        "source": "call_center",
        "report_1": {
            "title": "Multiple Collapse Incidents at City Marathon Event",
            "description": "Severe heat stroke and cardiac collapse reported near finish line. 4 runners unconscious, shallow breathing, high ambient temperature.",
            "source": "call_center",
            "lat": 12.9766,
            "lon": 77.5992
        },
        "report_2_duplicate": {
            "title": "Urgent Medical Assistance at Cubbon Park Marathon",
            "description": "Several people collapsed from heat exhaustion and chest pain at marathon finish area in Cubbon park. Need defibrillators and oxygen.",
            "source": "citizen",
            "lat": 12.9772,
            "lon": 77.5987  # ~85m away
        },
        "ai_triage": {
            "incident_type": "medical_emergency",
            "severity": "CRITICAL",
            "priority": "P1",
            "confidence": 0.97,
            "situation_summary": "Mass casualty heat distress event with multiple simultaneous cardiac and severe hyperthermia cases requiring rapid advanced resuscitation.",
            "people_at_risk": 12,
            "immediate_actions": [
                "Dispatch 3x Advanced Life Support (ALS) Ambulances with Mobile Defibrillators (AED)",
                "Deploy Mobile Medical Resuscitation Tent at Event Gate 2",
                "Distribute Rapid Electrolyte Hydration Packs and Cooling Mists",
                "Establish Emergency Green Corridor to Bowring Hospital"
            ],
            "recommended_resources": ["AMBULANCE", "MEDICAL_TEAM"]
        }
    },
    {
        "id": "gas_leak",
        "title": "Industrial Ammonia Chemical Gas Leak",
        "type": IncidentType.GAS_LEAK.value,
        "initial_severity": IncidentSeverity.CRITICAL.value,
        "initial_priority": IncidentPriority.P1.value,
        "address": "Peenya Industrial Complex Block B, Bangalore",
        "coordinates": [77.5308, 13.0283],
        "source": "iot",
        "report_1": {
            "title": "Toxic Anhydrous Ammonia Valve Rupture",
            "description": "High-pressure valve failure at cold storage chemical unit. Dense yellow ammonia gas plume detected by IoT sensors spreading downwind.",
            "source": "iot",
            "lat": 13.0283,
            "lon": 77.5308
        },
        "report_2_duplicate": {
            "title": "Pungent gas smell and coughing workers in Peenya Block B",
            "description": "Strong choking chemical gas coming from chemical plant next door in Peenya. Workers running out with burning eyes and throat irritation.",
            "source": "citizen",
            "lat": 13.0278,
            "lon": 77.5316  # ~100m away
        },
        "ai_triage": {
            "incident_type": "industrial_hazard",
            "severity": "CRITICAL",
            "priority": "P1",
            "confidence": 0.99,
            "situation_summary": "Hazardous toxic anhydrous ammonia release forming downwind vapor cloud. High inhalation toxicity with severe chemical burn risk within 500m radius.",
            "people_at_risk": 45,
            "immediate_actions": [
                "Dispatch Specialized HAZMAT Decontamination Unit with Level-A SCBA Suits",
                "Deploy Fire Water Curtains to knock down atmospheric ammonia vapor",
                "Execute 800m Downwind Mandatory Evacuation Order",
                "Issue Emergency Broadcast Siren for surrounding industrial sector"
            ],
            "recommended_resources": ["FIRE_TRUCK", "DISASTER_TEAM", "AMBULANCE"]
        }
    }
]


class SimulationEngine:
    """
    ResQAI Emergency Simulation Engine
    Orchestrates deterministic, end-to-end multi-step emergency response scenarios
    for real-time dashboard demos and SLA stress tests.
    """

    def __init__(self):
        self.is_running: bool = False
        self.task: Optional[asyncio.Task] = None
        self.current_scenario_id: Optional[str] = None
        self.current_scenario_title: Optional[str] = None
        self.current_stage: str = "IDLE"
        self.current_step_index: int = 0
        self.total_steps: int = 0
        self.started_at: Optional[datetime] = None
        self.speed_multiplier: float = 1.0
        self.step_delay_seconds: float = 3.0
        self.events_log: List[Dict[str, Any]] = []
        self.created_incident_ids: List[str] = []
        self.assigned_resource_ids: List[str] = []

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive live simulation status."""
        elapsed = 0
        if self.started_at and self.is_running:
            elapsed = int((datetime.now(timezone.utc) - self.started_at).total_seconds())

        return {
            "is_running": self.is_running,
            "current_scenario_id": self.current_scenario_id,
            "current_scenario_title": self.current_scenario_title,
            "current_stage": self.current_stage,
            "current_step_index": self.current_step_index,
            "total_steps": self.total_steps,
            "progress_percentage": round((self.current_step_index / max(1, self.total_steps)) * 100, 1) if self.total_steps > 0 else 0,
            "elapsed_seconds": elapsed,
            "speed_multiplier": self.speed_multiplier,
            "events_log": self.events_log[-50:],  # Return last 50 events
            "created_incident_ids": self.created_incident_ids,
            "assigned_resource_ids": self.assigned_resource_ids,
            "available_scenarios": [
                {
                    "id": sc["id"],
                    "title": sc["title"],
                    "type": sc["type"],
                    "severity": sc["initial_severity"],
                    "priority": sc["initial_priority"],
                    "address": sc["address"],
                    "description": sc["report_1"]["description"]
                }
                for sc in SIMULATION_SCENARIOS
            ]
        }

    def _log_event(
        self,
        event_type: str,
        stage: str,
        title: str,
        details: str,
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "INFO"
    ):
        """Append log event and broadcast WebSocket event."""
        log_entry = {
            "id": f"SIM-LOG-{len(self.events_log) + 1:04d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "stage": stage,
            "title": title,
            "details": details,
            "severity": severity,
            "scenario_id": self.current_scenario_id,
            "metadata": metadata or {}
        }
        self.events_log.insert(0, log_entry)  # Newest first
        if len(self.events_log) > 200:
            self.events_log.pop()
        return log_entry

    async def _safe_delay(self, seconds: float):
        """Sleep with speed multiplier applied."""
        actual_seconds = max(0.2, seconds / max(0.1, self.speed_multiplier))
        await asyncio.sleep(actual_seconds)

    async def start(
        self,
        db: AsyncIOMotorDatabase,
        scenario_id: Optional[str] = None,
        speed_multiplier: float = 1.0,
        auto_play_all: bool = False,
        step_delay_seconds: float = 3.0
    ):
        """Start the simulation background task."""
        if self.is_running:
            logger.warning("Simulation is already active. Stopping existing task first.")
            await self.stop()

        self.is_running = True
        self.speed_multiplier = max(0.25, min(10.0, speed_multiplier))
        self.step_delay_seconds = max(1.0, step_delay_seconds)
        self.started_at = datetime.now(timezone.utc)
        self.created_incident_ids = []
        self.assigned_resource_ids = []

        # Start async worker task
        self.task = asyncio.create_task(
            self._run_simulation_loop(db, scenario_id, auto_play_all)
        )
        return self.get_status()

    async def stop(self):
        """Stop the running simulation."""
        self.is_running = False
        self.current_stage = "STOPPED"
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        self._log_event(
            event_type="SIMULATION_STOPPED",
            stage="STOPPED",
            title="Simulation Terminated by Operator",
            details="Emergency Simulation Engine stopped gracefully.",
            severity="WARNING"
        )
        return self.get_status()

    async def reset(self, db: AsyncIOMotorDatabase):
        """Reset simulation state and release simulated resources."""
        await self.stop()

        # Reset assigned resources
        try:
            if self.assigned_resource_ids:
                await db.resources.update_many(
                    {"resource_id": {"$in": self.assigned_resource_ids}},
                    {"$set": {"status": ResourceStatus.AVAILABLE.value, "current_incident_id": None, "updated_at": datetime.now(timezone.utc)}}
                )
        except Exception as e:
            logger.error(f"Error resetting resources: {e}")

        self.current_scenario_id = None
        self.current_scenario_title = None
        self.current_stage = "IDLE"
        self.current_step_index = 0
        self.total_steps = 0
        self.started_at = None
        self.events_log = []
        self.created_incident_ids = []
        self.assigned_resource_ids = []

        self._log_event(
            event_type="SIMULATION_RESET",
            stage="IDLE",
            title="Simulation State Reset",
            details="Cleared event logs, reset telemetry metrics, and restored assigned fleet units to AVAILABLE status.",
            severity="INFO"
        )
        return self.get_status()

    async def _run_simulation_loop(
        self,
        db: AsyncIOMotorDatabase,
        scenario_id: Optional[str],
        auto_play_all: bool
    ):
        """Execute selected scenario or cycle through all scenarios sequentially."""
        try:
            scenarios_to_run = []
            if scenario_id:
                scenarios_to_run = [s for s in SIMULATION_SCENARIOS if s["id"] == scenario_id]
            if not scenarios_to_run:
                scenarios_to_run = SIMULATION_SCENARIOS if auto_play_all else [SIMULATION_SCENARIOS[0]]

            # Each scenario has 7 pipeline stages
            self.total_steps = len(scenarios_to_run) * 7
            self.current_step_index = 0

            for scenario in scenarios_to_run:
                if not self.is_running:
                    break
                await self._execute_scenario(db, scenario)
                if auto_play_all and self.is_running:
                    await self._safe_delay(self.step_delay_seconds * 1.5)

            self.current_stage = "COMPLETED"
            self.is_running = False
            self._log_event(
                event_type="SIMULATION_COMPLETED",
                stage="COMPLETED",
                title="Simulation Sequence Completed",
                details=f"All {len(scenarios_to_run)} scenarios finished execution successfully.",
                severity="INFO"
            )
        except asyncio.CancelledError:
            logger.info("Simulation task was cancelled.")
        except Exception as e:
            logger.error(f"Error during simulation execution: {e}", exc_info=True)
            self.is_running = False
            self.current_stage = "ERROR"
            self._log_event(
                event_type="SIMULATION_ERROR",
                stage="ERROR",
                title="Simulation Execution Error",
                details=str(e),
                severity="CRITICAL"
            )

    async def _execute_scenario(self, db: AsyncIOMotorDatabase, scenario: Dict[str, Any]):
        """Step through the complete 7-stage lifecycle of a single emergency scenario."""
        self.current_scenario_id = scenario["id"]
        self.current_scenario_title = scenario["title"]

        # =========================================================================
        # STAGE 1: CITIZEN 911 / IOT REPORT INGESTION
        # =========================================================================
        self.current_stage = "REPORT_INGESTION"
        self.current_step_index += 1
        rep1 = scenario["report_1"]
        now = datetime.now(timezone.utc)

        incident_doc = {
            "incident_id": f"INC-SIM-{random.randint(1000, 9999)}",
            "title": rep1["title"],
            "description": rep1["description"],
            "type": scenario["type"],
            "severity": scenario["initial_severity"],
            "priority": scenario["initial_priority"],
            "status": IncidentStatus.REPORTED.value,
            "source": rep1["source"],
            "reported_by": f"Simulated {rep1['source'].capitalize()} Caller",
            "address": scenario["address"],
            "location": {
                "type": "Point",
                "coordinates": scenario["coordinates"]
            },
            "reported_at": now,
            "updated_at": now,
            "duplicate_count": 0,
            "reports": [
                {
                    "report_id": f"REP-{random.randint(100, 999)}",
                    "title": rep1["title"],
                    "description": rep1["description"],
                    "source": rep1["source"],
                    "reported_at": now,
                    "location": {"latitude": rep1["lat"], "longitude": rep1["lon"]}
                }
            ],
            "timeline": [
                {
                    "timestamp": now,
                    "action": "Incident Reported",
                    "actor": rep1["source"].capitalize(),
                    "details": f"Initial 911/IoT report received: {rep1['title']}"
                }
            ],
            "assigned_resources": []
        }

        created_inc = await DBService.create_incident(db, incident_doc)
        incident_id = created_inc.get("incident_id")
        self.created_incident_ids.append(incident_id)

        # Broadcast real-time WebSocket event
        await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_CREATED, created_inc)

        self._log_event(
            event_type="INCIDENT_CREATED",
            stage="REPORT_INGESTION",
            title=f"Stage 1: Emergency Ingested [{incident_id}]",
            details=f"Received report '{rep1['title']}' via {rep1['source']}. Initial severity {scenario['initial_severity']}.",
            metadata={"incident_id": incident_id, "location": scenario["address"]},
            severity="INFO"
        )
        await self._safe_delay(self.step_delay_seconds)

        # =========================================================================
        # STAGE 2: AI TRIAGE, SEVERITY & PRIORITY CLASSIFICATION
        # =========================================================================
        self.current_stage = "AI_TRIAGE"
        self.current_step_index += 1

        ai_data = scenario["ai_triage"]
        update_data = {
            "ai_analysis": ai_data,
            "severity": ai_data["severity"],
            "priority": ai_data["priority"],
            "confidence": ai_data["confidence"],
            "status": IncidentStatus.VERIFIED.value,
            "updated_at": datetime.now(timezone.utc)
        }

        updated_inc = await DBService.update_incident(db, incident_id, update_data)
        if not updated_inc:
            updated_inc = created_inc

        # Broadcast real-time classification event
        await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_CLASSIFIED, {
            "incident_id": incident_id,
            "ai_analysis": ai_data,
            "severity": ai_data["severity"],
            "priority": ai_data["priority"],
            "confidence": ai_data["confidence"]
        })
        await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, updated_inc)

        # Trigger escalation alert if CRITICAL
        if ai_data["severity"] == "CRITICAL" or ai_data["priority"] == "P1":
            await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_ESCALATED, updated_inc)
            await AlertService.evaluate_incident_alerts(db, updated_inc)

        self._log_event(
            event_type="INCIDENT_CLASSIFIED",
            stage="AI_TRIAGE",
            title=f"Stage 2: AI Triage Analyzed [{ai_data['severity']} / {ai_data['priority']}]",
            details=f"AI Confidence: {int(ai_data['confidence']*100)}%. People at Risk: {ai_data['people_at_risk']}. {ai_data['situation_summary'][:120]}...",
            metadata={"confidence": ai_data["confidence"], "people_at_risk": ai_data["people_at_risk"]},
            severity="CRITICAL" if ai_data["severity"] == "CRITICAL" else "WARNING"
        )
        await self._safe_delay(self.step_delay_seconds)

        # =========================================================================
        # STAGE 3: INTENTIONAL DUPLICATE REPORT INJECTION & NLP/GEO DEDUP MERGING
        # =========================================================================
        self.current_stage = "DUPLICATE_DETECTION"
        self.current_step_index += 1
        rep2 = scenario["report_2_duplicate"]

        # 1. Run DuplicateDetector to confirm spatial & text similarity
        dedup_check = await DuplicateDetector.check_duplicate(
            db=db,
            title=rep2["title"],
            description=rep2["description"],
            latitude=rep2["lat"],
            longitude=rep2["lon"],
            reported_at=datetime.now(timezone.utc)
        )

        # 2. Merge duplicate call into parent incident
        merged_report_data = {
            "title": rep2["title"],
            "description": rep2["description"],
            "source": rep2["source"],
            "reported_at": datetime.now(timezone.utc),
            "location": {"latitude": rep2["lat"], "longitude": rep2["lon"]}
        }
        merged_doc = await DuplicateDetector.merge_duplicate_report(
            db=db,
            matched_incident_id=incident_id,
            new_report_data=merged_report_data,
            similarity_score=dedup_check.text_similarity or 0.88
        )

        self._log_event(
            event_type="INCIDENT_DUPLICATED",
            stage="DUPLICATE_DETECTION",
            title=f"Stage 3: Duplicate Merged (3-Signal NLP/Geo)",
            details=f"Secondary citizen call detected as duplicate (Distance: {int((dedup_check.distance_km or 0.08)*1000)}m, Text Match: {int((dedup_check.text_similarity or 0.88)*100)}%). Merged into {incident_id} without duplicate dispatch.",
            metadata={
                "duplicate_count": merged_doc.get("duplicate_count", 1) if merged_doc else 1,
                "distance_m": int((dedup_check.distance_km or 0.08)*1000),
                "text_similarity": dedup_check.text_similarity or 0.88
            },
            severity="WARNING"
        )
        await self._safe_delay(self.step_delay_seconds)

        # =========================================================================
        # STAGE 4: AI RESOURCE RECOMMENDATION & DISPATCH SCORING
        # =========================================================================
        self.current_stage = "RESOURCE_RECOMMENDATION"
        self.current_step_index += 1

        recommendations = await ResourceMatcher.recommend_resources_for_incident(
            db=db,
            incident_id=incident_id,
            limit=5
        )

        # If no active units available in DB, retrieve or dynamically synthesize a top unit
        selected_resource_id = None
        selected_resource_name = "Emergency Response Unit 01"
        selected_category = "AMBULANCE"
        match_score = 92.0

        if recommendations and len(recommendations) > 0:
            top_rec = recommendations[0]
            selected_resource_id = top_rec.resource_id
            selected_resource_name = top_rec.name
            selected_category = top_rec.category
            match_score = round(top_rec.score * 100, 1)
        else:
            # Fallback to finding any available resource in DB
            avail_res = await db.resources.find_one({"status": ResourceStatus.AVAILABLE.value})
            if avail_res:
                selected_resource_id = avail_res.get("resource_id", str(avail_res.get("_id")))
                selected_resource_name = avail_res.get("name", "Rapid Response Squad")
                selected_category = avail_res.get("category", "RESCUE_TEAM")
            else:
                # Create a quick simulated resource if database is empty
                sim_res_id = f"RES-SIM-{random.randint(100, 999)}"
                await db.resources.insert_one({
                    "resource_id": sim_res_id,
                    "name": f"Delta {scenario['type'].capitalize()} Squad",
                    "category": scenario["ai_triage"]["recommended_resources"][0] if scenario["ai_triage"]["recommended_resources"] else "RESCUE_TEAM",
                    "status": ResourceStatus.AVAILABLE.value,
                    "capabilities": ["FIRST_AID", "RAPID_RESPONSE", "HYDRAULIC_CUTTERS"],
                    "location": {"type": "Point", "coordinates": scenario["coordinates"]},
                    "address": "Command Sector Hub",
                    "updated_at": datetime.now(timezone.utc)
                })
                selected_resource_id = sim_res_id
                selected_resource_name = f"Delta {scenario['type'].capitalize()} Squad"
                selected_category = "RESCUE_TEAM"

        self._log_event(
            event_type="RESOURCE_MATCHED",
            stage="RESOURCE_RECOMMENDATION",
            title=f"Stage 4: AI Resource Ranking Computed",
            details=f"Optimal match selected: {selected_resource_name} ({selected_category}) with AI Dispatch Score {match_score}%.",
            metadata={"recommended_resource": selected_resource_name, "score": match_score},
            severity="INFO"
        )
        await self._safe_delay(self.step_delay_seconds)

        # =========================================================================
        # STAGE 5: RESOURCE ASSIGNMENT & DISPATCH
        # =========================================================================
        self.current_stage = "RESOURCE_ASSIGNMENT"
        self.current_step_index += 1

        if selected_resource_id:
            try:
                assign_res = await ResourceMatcher.assign_resource_to_incident(
                    db=db,
                    incident_id=incident_id,
                    resource_id=selected_resource_id,
                    actor="ResQAI Auto-Dispatch AI",
                    notes=f"Automated AI dispatch for simulated emergency {scenario['title']}"
                )
                self.assigned_resource_ids.append(selected_resource_id)
            except Exception as e:
                logger.warning(f"Resource assignment notice: {e}")

        # Update status to DISPATCHED
        await DBService.update_incident(db, incident_id, {
            "status": IncidentStatus.DISPATCHED.value,
            "updated_at": datetime.now(timezone.utc)
        })

        self._log_event(
            event_type="RESOURCE_ASSIGNED",
            stage="RESOURCE_ASSIGNMENT",
            title=f"Stage 5: Unit Dispatched [{selected_resource_name}]",
            details=f"{selected_resource_name} dispatched to {scenario['address']}. Vehicle telemetry en-route.",
            metadata={"resource_id": selected_resource_id, "incident_id": incident_id},
            severity="INFO"
        )
        await self._safe_delay(self.step_delay_seconds)

        # =========================================================================
        # STAGE 6: EN ROUTE & IN-PROGRESS EMERGENCY MITIGATION
        # =========================================================================
        self.current_stage = "IN_PROGRESS"
        self.current_step_index += 1

        in_prog_inc = await DBService.update_incident(db, incident_id, {
            "status": IncidentStatus.IN_PROGRESS.value,
            "updated_at": datetime.now(timezone.utc)
        })
        if in_prog_inc:
            await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, in_prog_inc)

        self._log_event(
            event_type="INCIDENT_IN_PROGRESS",
            stage="IN_PROGRESS",
            title=f"Stage 6: Field Team On Scene",
            details=f"{selected_resource_name} arrived on site. Immediate AI triage actions executed: {scenario['ai_triage']['immediate_actions'][0]}.",
            metadata={"incident_id": incident_id},
            severity="INFO"
        )
        await self._safe_delay(self.step_delay_seconds)

        # =========================================================================
        # STAGE 7: CONTAINMENT & RESOLUTION
        # =========================================================================
        self.current_stage = "RESOLUTION"
        self.current_step_index += 1

        resolved_inc = await DBService.update_incident(db, incident_id, {
            "status": IncidentStatus.RESOLVED.value,
            "updated_at": datetime.now(timezone.utc)
        })
        if resolved_inc:
            await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, resolved_inc)

        # Release resource back to AVAILABLE
        if selected_resource_id:
            try:
                await ResourceMatcher.release_resource(
                    db=db,
                    resource_id=selected_resource_id,
                    incident_id=incident_id,
                    actor="Incident Commander"
                )
            except Exception as e:
                logger.warning(f"Resource release notice: {e}")

        self._log_event(
            event_type="INCIDENT_RESOLVED",
            stage="RESOLUTION",
            title=f"Stage 7: Crisis Contained & Resolved",
            details=f"Incident {incident_id} successfully resolved. {selected_resource_name} released back to AVAILABLE standby fleet.",
            metadata={"incident_id": incident_id, "status": "RESOLVED"},
            severity="INFO"
        )

    # =========================================================================
    # DEDICATED 13-STEP DEMO MODE HANDLERS (IDEMPOTENT & REPEATABLE)
    # =========================================================================
    async def setup_demo_environment(self, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """
        Cleanly prepares database for a fresh 13-step judge demo run.
        Cleans up previous demo incidents and ensures nearby units exist.
        """
        # 1. Clean up previous demo incidents
        await db.incidents.delete_many({
            "$or": [
                {"incident_id": {"$regex": "^INC-DEMO"}},
                {"title": {"$regex": "Outer Ring Road|Bellandur"}},
                {"reported_by": "Demo Mode Judge Runner"}
            ]
        })

        # 2. Reset and ensure the 3 demo fleet units exist in AVAILABLE status
        demo_resources = [
            {
                "resource_id": "RES-DEMO-AMB-01",
                "name": "Advanced Trauma Ambulance Alpha-01",
                "category": ResourceCategory.AMBULANCE.value,
                "status": ResourceStatus.AVAILABLE.value,
                "capabilities": ["AMBULANCE", "ALS", "AED", "VENTILATOR", "PARAMEDIC", "TRAUMA_KIT"],
                "location": {"type": "Point", "coordinates": [77.6690, 12.9290]},  # ~1.1km from crash
                "address": "Bellandur Emergency Dispatch Station",
                "current_incident_id": None,
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "resource_id": "RES-DEMO-POL-04",
                "name": "Traffic Police Rapid Patrol 04",
                "category": ResourceCategory.POLICE.value,
                "status": ResourceStatus.AVAILABLE.value,
                "capabilities": ["POLICE", "TRAFFIC_DIVERSION", "CROWD_CONTROL", "FIRST_AID"],
                "location": {"type": "Point", "coordinates": [77.6710, 12.9230]},  # ~0.8km from crash
                "address": "Outer Ring Road Sector Outpost",
                "current_incident_id": None,
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "resource_id": "RES-DEMO-FIR-02",
                "name": "Heavy Hydraulic Extrication Rescue 02",
                "category": ResourceCategory.FIRE_TRUCK.value,
                "status": ResourceStatus.AVAILABLE.value,
                "capabilities": ["FIRE_TRUCK", "HYDRAULIC_CUTTERS", "EXTRICATION", "FOAM_SUPPRESSION", "HEAVY_RESCUE"],
                "location": {"type": "Point", "coordinates": [77.6620, 12.9350]},  # ~2.0km from crash
                "address": "Central Fire & Rescue Station 02",
                "current_incident_id": None,
                "updated_at": datetime.now(timezone.utc)
            }
        ]

        for r in demo_resources:
            await db.resources.update_one(
                {"resource_id": r["resource_id"]},
                {"$set": r},
                upsert=True
            )

        return {
            "status": "demo_environment_ready",
            "message": "Demo mode environment initialized. Cleaned up past runs and seeded 3 ready fleet units.",
            "demo_incident_id": "INC-DEMO-ROAD-101"
        }

    async def execute_demo_step(self, db: AsyncIOMotorDatabase, step: int) -> Dict[str, Any]:
        """
        Executes a single step (1 to 13) in the dedicated Judge Demo Mode sequence.
        100% deterministic, self-contained, and repeatable.
        """
        now = datetime.now(timezone.utc)
        demo_id = "INC-DEMO-ROAD-101"

        if step == 1:
            # STEP 1: Show dashboard with active incidents & clean environment
            await self.setup_demo_environment(db)
            active_count = await db.incidents.count_documents({"status": {"$in": ["REPORTED", "VERIFIED", "DISPATCHED", "IN_PROGRESS"]}})
            avail_res_count = await db.resources.count_documents({"status": "AVAILABLE"})
            return {
                "step": 1,
                "step_title": "Overview: Active Incidents & Standby Fleet",
                "description": "Dashboard HUD initialized with live incident streams and ready fleet telemetry.",
                "data": {
                    "active_incidents": active_count,
                    "available_resources": avail_res_count,
                    "system_status": "ONLINE"
                }
            }

        elif step == 2:
            # STEP 2: Create critical road accident report
            doc = {
                "incident_id": demo_id,
                "title": "Major Highway Multi-Vehicle Collision & Pileup",
                "description": "Passenger bus collided with two sedans during heavy rush hour traffic on Outer Ring Road flyover. Overturned vehicle, 18 passengers trapped, fuel leaking across 2 lanes.",
                "type": IncidentType.ROAD_ACCIDENT.value,
                "severity": IncidentSeverity.CRITICAL.value,
                "priority": IncidentPriority.P1.value,
                "status": IncidentStatus.REPORTED.value,
                "source": "citizen",
                "reported_by": "Citizen Emergency Hotline",
                "address": "Outer Ring Road Flyover, Bellandur, Bangalore",
                "location": {
                    "type": "Point",
                    "coordinates": [77.6745, 12.9252]
                },
                "reported_at": now,
                "updated_at": now,
                "duplicate_count": 0,
                "reports": [
                    {
                        "report_id": "REP-DEMO-001",
                        "title": "Major Highway Multi-Vehicle Collision",
                        "description": "Passenger bus collided with two sedans. Overturned vehicle, fuel leak.",
                        "source": "citizen",
                        "reported_at": now,
                        "location": {"latitude": 12.9252, "longitude": 77.6745}
                    }
                ],
                "timeline": [
                    {
                        "timestamp": now,
                        "action": "Citizen 911 Call Received",
                        "actor": "Emergency Hotline",
                        "details": "High-velocity multi-vehicle collision reported at Outer Ring Road"
                    }
                ],
                "assigned_resources": []
            }
            created = await DBService.create_incident(db, doc)
            await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_CREATED, created)
            return {
                "step": 2,
                "step_title": "Incident Ingestion: Critical Road Accident",
                "description": "911 citizen call ingested for Outer Ring Road collision with 18 passengers trapped.",
                "data": created
            }

        elif step == 3:
            # STEP 3: AI classifies Road Accident, CRITICAL, P1
            ai_data = {
                "incident_type": "road_accident",
                "severity": "CRITICAL",
                "priority": "P1",
                "confidence": 0.96,
                "situation_summary": "High-velocity multi-vehicle collision with overturned passenger bus and high risk of secondary vehicle fire from fuel leakage. Critical trauma extrication required.",
                "people_at_risk": 18,
                "immediate_actions": [
                    "Dispatch Heavy Hydraulic Extrication Fire Truck",
                    "Deploy Advanced Life Support (ALS) Trauma Ambulances",
                    "Activate Traffic Police for 500m arterial road perimeter diversion",
                    "Alert St. John's Level-1 Trauma Emergency Center"
                ],
                "recommended_resources": ["AMBULANCE", "FIRE_TRUCK", "POLICE"]
            }
            updated = await DBService.update_incident(db, demo_id, {
                "ai_analysis": ai_data,
                "severity": "CRITICAL",
                "priority": "P1",
                "confidence": 0.96,
                "status": IncidentStatus.VERIFIED.value,
                "updated_at": now
            })
            await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_CLASSIFIED, {
                "incident_id": demo_id,
                "ai_analysis": ai_data,
                "severity": "CRITICAL",
                "priority": "P1",
                "confidence": 0.96
            })
            await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_ESCALATED, updated or {})
            return {
                "step": 3,
                "step_title": "AI Classification: Road Accident | CRITICAL | P1",
                "description": "ResQAI NLP engine classified emergency as CRITICAL P1 with 96% AI confidence.",
                "data": {
                    "incident_id": demo_id,
                    "type": "road_accident",
                    "severity": "CRITICAL",
                    "priority": "P1",
                    "confidence": 0.96
                }
            }

        elif step == 4:
            # STEP 4: AI generates summary and immediate actions
            inc = await DBService.get_incident(db, demo_id)
            ai_analysis = inc.get("ai_analysis", {}) if inc else {}
            return {
                "step": 4,
                "step_title": "AI Situation Summary & Immediate Action Checklist",
                "description": "Structured AI briefing extracted 18 people at risk and formulated 4 immediate critical response actions.",
                "data": {
                    "situation_summary": ai_analysis.get("situation_summary", "Critical highway pileup with overturned bus"),
                    "people_at_risk": ai_analysis.get("people_at_risk", 18),
                    "immediate_actions": ai_analysis.get("immediate_actions", [
                        "Dispatch Heavy Hydraulic Extrication Fire Truck",
                        "Deploy Advanced Life Support (ALS) Trauma Ambulances",
                        "Activate Traffic Police for 500m arterial road perimeter diversion",
                        "Alert St. John's Level-1 Trauma Emergency Center"
                    ])
                }
            }

        elif step == 5:
            # STEP 5: System recommends nearest ambulance, police, and rescue team
            recommendations = await ResourceMatcher.recommend_resources_for_incident(db, demo_id, limit=5)
            rec_list = [r.model_dump() for r in recommendations] if recommendations else [
                {"resource_id": "RES-DEMO-AMB-01", "name": "Advanced Trauma Ambulance Alpha-01", "category": "AMBULANCE", "score": 0.95, "distance_km": 1.1, "readiness": "AVAILABLE"},
                {"resource_id": "RES-DEMO-POL-04", "name": "Traffic Police Rapid Patrol 04", "category": "POLICE", "score": 0.92, "distance_km": 0.8, "readiness": "AVAILABLE"},
                {"resource_id": "RES-DEMO-FIR-02", "name": "Heavy Hydraulic Extrication Rescue 02", "category": "FIRE_TRUCK", "score": 0.89, "distance_km": 2.0, "readiness": "AVAILABLE"}
            ]
            return {
                "step": 5,
                "step_title": "AI Resource Scoring & Recommendation",
                "description": "Geospatial proximity, capability matrix, and readiness evaluated to score top 3 emergency response units.",
                "data": {
                    "recommendations": rec_list
                }
            }

        elif step == 6:
            # STEP 6: Assign resources
            assigned_units = ["RES-DEMO-AMB-01", "RES-DEMO-POL-04", "RES-DEMO-FIR-02"]
            for r_id in assigned_units:
                try:
                    await ResourceMatcher.assign_resource_to_incident(
                        db=db,
                        incident_id=demo_id,
                        resource_id=r_id,
                        actor="ResQAI Auto-Dispatch AI",
                        notes="Dispatched to Outer Ring Road Critical Collision"
                    )
                except Exception as e:
                    logger.warning(f"Demo assign error: {e}")

            updated = await DBService.update_incident(db, demo_id, {
                "status": IncidentStatus.DISPATCHED.value,
                "updated_at": now
            })
            if updated:
                await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, updated)

            return {
                "step": 6,
                "step_title": "Multi-Unit Resource Dispatch",
                "description": "Ambulance Alpha-01, Police Patrol 04, and Fire Rescue 02 dispatched. Fleet unit statuses set to BUSY.",
                "data": {
                    "incident_id": demo_id,
                    "status": "DISPATCHED",
                    "assigned_resources": assigned_units
                }
            }

        elif step == 7:
            # STEP 7: Map updates
            inc = await DBService.get_incident(db, demo_id)
            res_list = await db.resources.find({"resource_id": {"$in": ["RES-DEMO-AMB-01", "RES-DEMO-POL-04", "RES-DEMO-FIR-02"]}}).to_list(10)
            return {
                "step": 7,
                "step_title": "Tactical Map Telemetry Synchronized",
                "description": "Incident marker updated with critical red glow and vehicle GPS coordinates plotted en route.",
                "data": {
                    "incident_location": inc.get("location") if inc else {"type": "Point", "coordinates": [77.6745, 12.9252]},
                    "active_units": [clean_mongo_doc(r) for r in res_list]
                }
            }

        elif step == 8:
            # STEP 8: Generate second citizen report for same accident
            rep2 = {
                "title": "Severe road crash near Bellandur flyover",
                "description": "Flipped bus and crushed cars blocking Outer Ring Road. Multiple passengers trapped, urgent ambulances and fire truck needed.",
                "source": "citizen",
                "lat": 12.9258,
                "lon": 77.6751,  # ~80m away
                "reported_at": now
            }
            return {
                "step": 8,
                "step_title": "Secondary Citizen 911 Call Ingested",
                "description": "Another citizen calls 20s later reporting the same accident from adjacent flyover ramp.",
                "data": rep2
            }

        elif step == 9:
            # STEP 9: Duplicate detection identifies related report
            dedup_check = await DuplicateDetector.check_duplicate(
                db=db,
                title="Severe road crash near Bellandur flyover",
                description="Flipped bus and crushed cars blocking Outer Ring Road. Multiple passengers trapped, urgent ambulances and fire truck needed.",
                latitude=12.9258,
                longitude=77.6751,
                reported_at=now
            )
            return {
                "step": 9,
                "step_title": "3-Signal Deduplication Match Identified",
                "description": "Spatial distance (80m), temporal window (20s), and TF-IDF text similarity (88%) confirmed duplicate match.",
                "data": {
                    "is_duplicate": True,
                    "matched_incident_id": demo_id,
                    "distance_km": dedup_check.distance_km or 0.08,
                    "text_similarity": dedup_check.text_similarity or 0.88,
                    "confidence": dedup_check.confidence or 0.94
                }
            }

        elif step == 10:
            # STEP 10: Reports merge
            merged_report = {
                "title": "Severe road crash near Bellandur flyover",
                "description": "Flipped bus and crushed cars blocking Outer Ring Road. Multiple passengers trapped, urgent ambulances and fire truck needed.",
                "source": "citizen",
                "reported_at": now,
                "location": {"latitude": 12.9258, "longitude": 77.6751}
            }
            merged_doc = await DuplicateDetector.merge_duplicate_report(
                db=db,
                matched_incident_id=demo_id,
                new_report_data=merged_report,
                similarity_score=0.88
            )
            return {
                "step": 10,
                "step_title": "Automated Report Merge & Deduplication",
                "description": "Secondary call merged into master incident. Duplicate counter incremented without double-dispatching resources.",
                "data": {
                    "incident_id": demo_id,
                    "duplicate_count": merged_doc.get("duplicate_count", 1) if merged_doc else 1,
                    "reports_total": len(merged_doc.get("reports", [])) if merged_doc else 2
                }
            }

        elif step == 11:
            # STEP 11: Show notification
            notif_msg = "Duplicate Emergency Call Merged: 3-Signal NLP/Geo deduplication prevented redundant fleet dispatch for Outer Ring Road collision."
            notif = {
                "alert_id": f"ALT-DEMO-{random.randint(100, 999)}",
                "type": "DUPLICATE_MERGED",
                "severity": "INFO",
                "incident_id": demo_id,
                "message": notif_msg,
                "created_at": now,
                "read": False
            }
            await db.notifications.insert_one(notif)
            clean_notif = clean_mongo_doc(notif)
            await ws_manager.broadcast_event(WebSocketEventType.NOTIFICATION_CREATED, clean_notif)
            return {
                "step": 11,
                "step_title": "Real-time Notification Broadcast",
                "description": "Tactical HUD alert notification dispatched to all command operators via WebSocket bus.",
                "data": clean_notif
            }

        elif step == 12:
            # STEP 12: Resolve incident & release units
            resolved_inc = await DBService.update_incident(db, demo_id, {
                "status": IncidentStatus.RESOLVED.value,
                "updated_at": now
            })
            if resolved_inc:
                await ws_manager.broadcast_event(WebSocketEventType.INCIDENT_UPDATED, resolved_inc)

            # Release the 3 units back to AVAILABLE
            assigned_units = ["RES-DEMO-AMB-01", "RES-DEMO-POL-04", "RES-DEMO-FIR-02"]
            for r_id in assigned_units:
                try:
                    await ResourceMatcher.release_resource(
                        db=db,
                        resource_id=r_id,
                        incident_id=demo_id,
                        actor="Incident Commander"
                    )
                except Exception as e:
                    logger.warning(f"Demo release error: {e}")

            return {
                "step": 12,
                "step_title": "Crisis Resolution & Fleet Standby Release",
                "description": "Casualties extricated, highway lanes cleared. Incident marked RESOLVED and all 3 units returned to AVAILABLE standby.",
                "data": {
                    "incident_id": demo_id,
                    "status": "RESOLVED",
                    "released_resources": assigned_units
                }
            }

        elif step == 13:
            # STEP 13: Analytics update
            from backend.app.routes.analytics import get_overview_analytics
            overview_stats = await get_overview_analytics(db)
            return {
                "step": 13,
                "step_title": "Executive Analytics & SLA Telemetry Recomputed",
                "description": "MongoDB aggregation pipelines recalculated live KPIs: resolved count incremented, duplicate calls prevented recorded.",
                "data": overview_stats
            }

        return {"step": step, "step_title": "Unknown Step", "description": "No action executed."}


# Singleton Instance
simulation_engine = SimulationEngine()

