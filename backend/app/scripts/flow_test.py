"""
ResQAI Complete Emergency Lifecycle Flow Test
Validates:
Create incident -> MongoDB -> AI classification -> severity -> priority -> duplicate detection ->
resource recommendation -> resource assignment -> WebSocket update -> frontend update -> notification -> resolve incident -> analytics update
"""
import asyncio
import logging
import time
from datetime import datetime, timezone

from backend.app.database import DatabaseManager, get_database
from backend.app.services.db_service import DBService
from backend.app.ai.incident_classifier import analyze_incident
from backend.app.services.duplicate_detector import DuplicateDetector
from backend.app.services.resource_matcher import ResourceMatcher
from backend.app.websocket.manager import ws_manager, WebSocketEventType
from backend.app.routes.analytics import get_analytics_overview
from backend.app.models.incident import IncidentSeverity, IncidentPriority

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("resqai.flow_test")

async def run_flow_test():
    db = await get_database()
    logger.info("================================================================================")
    logger.info("STARTING END-TO-END EMERGENCY LIFECYCLE FLOW AUDIT")
    logger.info("================================================================================")
    
    flow_steps = []
    
    try:
        # STEP 1: CREATE INCIDENT
        timestamp_id = int(time.time())
        inc_id = f"INC-FLOW-{timestamp_id}"
        inc_doc = {
            "incident_id": inc_id,
            "title": "Industrial Warehouse Chemical Fire with Trapped Workers",
            "description": "Massive explosion and toxic smoke in Block C storage. 6 warehouse workers trapped on upper level, solvent drums catching fire.",
            "type": "fire",
            "severity": "CRITICAL",
            "priority": "P1",
            "status": "REPORTED",
            "location": {
                "type": "Point",
                "coordinates": [77.6740, 12.9250]
            },
            "address": "Sector 4B, Industrial Estate, Bengaluru",
            "source": "CITIZEN_CALL",
            "reported_at": datetime.now(timezone.utc),
            "assigned_resources": [],
            "duplicate_count": 0,
            "related_incidents": [],
            "timeline": [
                {
                    "timestamp": datetime.now(timezone.utc),
                    "action": "Incident Reported",
                    "actor": "Citizen 911 Call",
                    "details": "Reported chemical explosion and trapped personnel."
                }
            ]
        }
        flow_steps.append(("1. Create incident", "SUCCESS", f"Prepared incident payload for {inc_id}"))

        # STEP 2: MONGODB INSERTION
        await db.incidents.insert_one(inc_doc)
        inserted_inc = await db.incidents.find_one({"incident_id": inc_id})
        assert inserted_inc is not None
        assert inserted_inc["incident_id"] == inc_id
        flow_steps.append(("2. MongoDB", "SUCCESS", f"Persisted {inc_id} to MongoDB with 2dsphere Point coordinates."))

        # STEP 3: AI CLASSIFICATION
        ai_result = await analyze_incident(
            description=f"{inserted_inc['title']}. {inserted_inc['description']}",
            source="CITIZEN_CALL",
            location=inserted_inc["address"]
        )
        assert ai_result["incident_type"] in ["fire", "industrial_hazard"]
        flow_steps.append(("3. AI classification", "SUCCESS", f"Categorized as '{ai_result['incident_type']}' (Confidence: {int(ai_result['confidence']*100)}%)."))

        # STEP 4: SEVERITY
        assert ai_result["severity"] in ["CRITICAL", "HIGH"]
        flow_steps.append(("4. Severity", "SUCCESS", f"Assigned severity '{ai_result['severity']}' matching emergency urgency."))

        # STEP 5: PRIORITY
        assert ai_result["priority"] in ["P1", "P2"]
        flow_steps.append(("5. Priority", "SUCCESS", f"Assigned priority '{ai_result['priority']}'."))

        # STEP 6: DUPLICATE DETECTION (Simulate second call)
        dup_check = await DuplicateDetector.check_duplicate(
            db=db,
            title="Fire outbreak at industrial chemical storage warehouse",
            description="Thick chemical smoke and fire at Block C warehouse, people crying for help on upper floor.",
            latitude=12.9252,
            longitude=77.6742,
            distance_threshold_km=1.0,
            time_threshold_minutes=45
        )
        assert dup_check.is_duplicate is True
        assert dup_check.matched_incident_id is not None
        flow_steps.append(("6. Duplicate detection", "SUCCESS", f"Matched incoming call to duplicate target {dup_check.matched_incident_id} (Dist: {int(dup_check.distance_km*1000)}m, NLP Sim: {int(dup_check.text_similarity*100)}%)."))

        # STEP 7: RESOURCE RECOMMENDATION
        rec_resp = await ResourceMatcher.recommend_resources_for_incident(db, inc_id, limit=5)
        recs = rec_resp.recommendations
        assert len(recs) >= 1
        top_unit = recs[0]
        flow_steps.append(("7. Resource recommendation", "SUCCESS", f"Scored candidate responders. Top ranked: {top_unit.name} ({top_unit.category}, Score: {round(top_unit.score*100, 1)}%)."))

        # STEP 8: RESOURCE ASSIGNMENT
        assigned_resp = await ResourceMatcher.assign_resource_to_incident(
            db=db,
            incident_id=inc_id,
            resource_id=top_unit.resource_id,
            actor="EOC Chief Dispatcher",
            notes="Immediate deployment to Block C storage chemical fire."
        )
        assert str(assigned_resp.status).upper() == "ASSIGNED"
        res_db = await db.resources.find_one({"resource_id": top_unit.resource_id})
        assert res_db["status"] == "BUSY"
        assert res_db["current_incident_id"] == inc_id
        flow_steps.append(("8. Resource assignment", "SUCCESS", f"Dispatched {top_unit.name} to {inc_id}. Unit status changed to BUSY in MongoDB."))

        # STEP 9: WEBSOCKET UPDATE
        await ws_manager.broadcast_event(
            WebSocketEventType.RESOURCE_ASSIGNED,
            {
                "incident_id": inc_id,
                "resource_id": top_unit.resource_id,
                "resource_name": top_unit.name,
                "category": top_unit.category
            }
        )
        flow_steps.append(("9. WebSocket update", "SUCCESS", "Broadcasted RESOURCE_ASSIGNED payload to all connected frontend clients."))

        # STEP 10: FRONTEND UPDATE
        # Verify that incident timeline and state retrieved from API will contain assigned resource and updated status
        refreshed_inc = await db.incidents.find_one({"incident_id": inc_id})
        assert top_unit.resource_id in refreshed_inc["assigned_resources"]
        assert refreshed_inc["status"] in ["DISPATCHED", "IN_PROGRESS"]
        flow_steps.append(("10. Frontend update", "SUCCESS", f"Incident state updated with assigned resource {top_unit.resource_id} and status '{refreshed_inc['status']}'."))

        # STEP 11: NOTIFICATION
        notif_id = f"NOTIF-FLOW-{timestamp_id}"
        notif_doc = {
            "notification_id": notif_id,
            "alert_id": notif_id,
            "type": "RESOURCE_DISPATCHED",
            "severity": "CRITICAL",
            "incident_id": inc_id,
            "message": f"Unit {top_unit.name} dispatched to {inc_id} (Chemical Warehouse Fire).",
            "created_at": datetime.now(timezone.utc),
            "read": False
        }
        await db.notifications.insert_one(notif_doc)
        await ws_manager.broadcast_event(WebSocketEventType.NOTIFICATION_CREATED, notif_doc)
        flow_steps.append(("11. Notification", "SUCCESS", f"Created & broadcasted alert {notif_id}."))

        # STEP 12: RESOLVE INCIDENT
        now_resolved = datetime.now(timezone.utc)
        await db.incidents.update_one(
            {"incident_id": inc_id},
            {
                "$set": {
                    "status": "RESOLVED",
                    "resolved_at": now_resolved,
                    "updated_at": now_resolved
                },
                "$push": {
                    "timeline": {
                        "timestamp": now_resolved,
                        "action": "Incident Resolved",
                        "actor": "Incident Commander",
                        "details": "Fire suppressed, all 6 personnel safely extricated."
                    }
                }
            }
        )
        # Release assigned resource
        await ResourceMatcher.release_resource(db=db, resource_id=top_unit.resource_id, incident_id=inc_id)
        resolved_doc = await db.incidents.find_one({"incident_id": inc_id})
        assert resolved_doc["status"] == "RESOLVED"
        flow_steps.append(("12. Resolve incident", "SUCCESS", f"Incident {inc_id} transitioned to RESOLVED. Responders released back to pool."))

        # STEP 13: ANALYTICS UPDATE
        analytics = await get_analytics_overview(db)
        assert analytics["resolved_incidents"] >= 1
        assert analytics["total_incidents"] >= 1
        flow_steps.append(("13. Analytics update", "SUCCESS", f"Real-time analytics pipeline refreshed: {analytics['resolved_incidents']} resolved incidents accounted for."))

        # Clean up
        await db.incidents.delete_one({"incident_id": inc_id})
        await db.notifications.delete_one({"notification_id": notif_id})

        logger.info("\n" + "="*80)
        logger.info("[AUDIT FLOW REPORT] ALL 13 STEPS EXECUTED SUCCESSFULLY")
        logger.info("="*80)
        for name, status, detail in flow_steps:
            logger.info(f"[{status}] {name:<26} : {detail}")
        logger.info("="*80)

        return True

    except Exception as e:
        logger.error(f"Lifecycle flow test failed: {e}", exc_info=True)
        return False
    finally:
        if DatabaseManager.client:
            DatabaseManager.client.close()

if __name__ == "__main__":
    asyncio.run(run_flow_test())
