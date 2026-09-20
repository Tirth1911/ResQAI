import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from bson import ObjectId

from backend.app.models.resource import ResourceStatus, ResourceCategory
from backend.app.utils.geo import haversine_distance_km
from backend.app.websocket.manager import ws_manager

logger = logging.getLogger("resqai.resource_matcher")

# Realistic Incident Type -> Required Capabilities / Categories Mapping
INCIDENT_CAPABILITY_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "fire": {
        "primary_categories": ["FIRE_TRUCK", "AMBULANCE", "POLICE"],
        "required_capabilities": ["FIRE_TRUCK", "FIRE_SUPPRESSION", "RESCUE", "FOAM_SUPPRESSION", "WATER_BOWSER"],
    },
    "medical_emergency": {
        "primary_categories": ["AMBULANCE", "MEDICAL_TEAM"],
        "required_capabilities": ["AMBULANCE", "MEDICAL_TEAM", "ICU_TRANSPORT", "AED", "VENTILATOR", "PARAMEDIC", "TRAUMA_KIT"],
    },
    "flood": {
        "primary_categories": ["RESCUE_TEAM", "DISASTER_TEAM", "AMBULANCE"],
        "required_capabilities": ["RESCUE_TEAM", "BOAT", "DISASTER_TEAM", "WATER_RESCUE", "DIVING", "SONAR", "LIFE_JACKETS"],
    },
    "road_accident": {
        "primary_categories": ["AMBULANCE", "POLICE", "RESCUE_TEAM", "FIRE_TRUCK"],
        "required_capabilities": ["AMBULANCE", "POLICE", "RESCUE_TEAM", "HYDRAULIC_CUTTERS", "EXTRICATION", "TRAFFIC_DIVERSION"],
    },
    "industrial_hazard": {
        "primary_categories": ["DISASTER_TEAM", "FIRE_TRUCK", "AMBULANCE"],
        "required_capabilities": ["FIRE_TRUCK", "HAZMAT", "RESCUE_TEAM", "CHEMICAL_NEUTRALIZATION", "SCBA", "GAS_DETECTION"],
    },
    "building_collapse": {
        "primary_categories": ["RESCUE_TEAM", "DISASTER_TEAM", "FIRE_TRUCK", "AMBULANCE"],
        "required_capabilities": ["RESCUE_TEAM", "DISASTER_TEAM", "HEAVY_RESCUE", "HYDRAULIC_CRANE", "CANINE", "USAR"],
    },
    "gas_leak": {
        "primary_categories": ["DISASTER_TEAM", "FIRE_TRUCK", "POLICE"],
        "required_capabilities": ["HAZMAT", "GAS_DETECTION", "SCBA", "PIPELINE_CLAMPING", "FOAM_CANNONS"],
    },
    "earthquake": {
        "primary_categories": ["DISASTER_TEAM", "RESCUE_TEAM", "MEDICAL_TEAM"],
        "required_capabilities": ["DISASTER_TEAM", "RESCUE_TEAM", "MEDICAL_TEAM", "STRUCTURAL_SAR", "SATELLITE_COMMS"],
    },
    "other": {
        "primary_categories": ["POLICE", "AMBULANCE"],
        "required_capabilities": ["RAPID_RESPONSE", "FIRST_AID"],
    }
}


# =============================================================================
# 1. SCHEMAS
# =============================================================================

class ResourceRecommendation(BaseModel):
    resource_id: str
    name: str
    category: str
    distance_km: float
    capability_match: float
    readiness: float
    score: float
    reason: str
    status: str
    capacity: int
    eta_min: Optional[float] = None
    location_name: Optional[str] = None


class IncidentRecommendationsResponse(BaseModel):
    incident_id: str
    incident_type: str
    severity: str
    priority: str
    recommendations: List[ResourceRecommendation]


class AssignResourceRequest(BaseModel):
    resource_id: str = Field(..., description="Resource ID to assign (e.g. RES-2001)")
    actor: str = Field(default="Command Dispatcher", description="Dispatcher or system assigning the resource")
    notes: Optional[str] = Field(default=None, description="Operational dispatch notes")


class AssignResourceResponse(BaseModel):
    status: str = "assigned"
    incident_id: str
    resource_id: str
    resource_name: str
    assigned_resources: List[str]
    message: str


class ReleaseResourceResponse(BaseModel):
    status: str = "released"
    resource_id: str
    resource_name: str
    new_status: str = "AVAILABLE"
    message: str


# =============================================================================
# 2. RESOURCE MATCHER ENGINE
# =============================================================================

class ResourceMatcher:

    @classmethod
    def get_readiness_score(cls, status: str) -> float:
        """Map resource operational status to readiness weight."""
        status_upper = status.upper() if status else "AVAILABLE"
        if status_upper == "AVAILABLE":
            return 1.0
        elif status_upper in ["EN_ROUTE", "RETURNING"]:
            return 0.5
        elif status_upper in ["BUSY", "ON_SCENE"]:
            return 0.2
        return 0.0  # OFFLINE / MAINTENANCE

    @classmethod
    def calculate_capability_match(
        cls,
        resource_category: str,
        resource_capabilities: List[str],
        incident_type: str,
        custom_required_capabilities: Optional[List[str]] = None
    ) -> float:
        """Calculate capability percentage overlap between resource and incident requirements."""
        mapping = INCIDENT_CAPABILITY_MAPPINGS.get(incident_type.lower(), INCIDENT_CAPABILITY_MAPPINGS["other"])
        target_caps = custom_required_capabilities or mapping["required_capabilities"]
        primary_cats = mapping["primary_categories"]

        # Normalize strings
        res_caps_normalized = {c.strip().upper() for c in resource_capabilities}
        res_caps_normalized.add(resource_category.strip().upper())
        target_caps_normalized = {c.strip().upper() for c in target_caps}

        # Check category alignment bonus
        category_aligned = resource_category.upper() in [c.upper() for c in primary_cats]

        # Calculate capability overlap
        overlap = len(res_caps_normalized & target_caps_normalized)
        base_match = overlap / max(1, len(target_caps_normalized))

        if category_aligned:
            # High alignment for designated emergency vehicle category
            return round(min(1.0, max(0.80, base_match + 0.40)), 2)

        return round(min(1.0, base_match), 2)

    @classmethod
    async def recommend_resources_for_incident(
        cls,
        db: AsyncIOMotorDatabase,
        incident_id: str,
        top_k: int = 5,
        limit: Optional[int] = None
    ) -> IncidentRecommendationsResponse:
        """
        Rank emergency responders using weighted scoring:
        score = (distance_score * 0.50) + (capability_match * 0.30) + (readiness * 0.20)
        """
        k = limit if limit is not None else top_k
        # 1. Fetch Incident from MongoDB
        query = {"incident_id": incident_id}
        if ObjectId.is_valid(incident_id):
            query = {"$or": [{"incident_id": incident_id}, {"_id": ObjectId(incident_id)}]}

        incident = await db.incidents.find_one(query)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found.")

        coords = incident.get("location", {}).get("coordinates", [])
        if len(coords) < 2:
            raise ValueError(f"Incident '{incident_id}' is missing valid location coordinates.")

        inc_lon, inc_lat = coords[0], coords[1]
        inc_type = str(incident.get("type", "other")).lower()
        severity = str(incident.get("severity", "MEDIUM"))
        priority = str(incident.get("priority", "P3"))

        # 2. Query MongoDB for candidate resources sorted by 2dsphere proximity (up to 75 km)
        cursor = db.resources.find({
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [inc_lon, inc_lat]
                    },
                    "$maxDistance": 75000.0  # 75km radius
                }
            }
        }).limit(30)

        candidates: List[ResourceRecommendation] = []

        async for res in cursor:
            res_coords = res.get("location", {}).get("coordinates", [])
            if len(res_coords) < 2:
                continue

            r_lon, r_lat = res_coords[0], res_coords[1]
            dist_km = round(haversine_distance_km(inc_lat, inc_lon, r_lat, r_lon), 2)

            res_id = res.get("resource_id", str(res.get("_id")))
            res_name = res.get("name", "Responder Unit")
            category = str(res.get("category", "AMBULANCE"))
            status = str(res.get("status", "AVAILABLE"))
            capacity = int(res.get("capacity", 1))
            capabilities = res.get("capabilities", [])

            # Component 1: Distance score (decay normalized over 50 km)
            distance_score = max(0.0, round(1.0 - (dist_km / 50.0), 3))

            # Component 2: Capability match
            capability_match = cls.calculate_capability_match(
                resource_category=category,
                resource_capabilities=capabilities,
                incident_type=inc_type
            )

            # Component 3: Readiness score
            readiness = cls.get_readiness_score(status)

            # Final Weighted Formula
            final_score = round(
                (distance_score * 0.50) +
                (capability_match * 0.30) +
                (readiness * 0.20),
                3
            )

            # Generate Explainable Reason
            if readiness == 1.0 and capability_match >= 0.8:
                reason = f"Closest available {category.lower().replace('_', ' ')} ({dist_km} km) with high operational capability match ({int(capability_match * 100)}%)."
            elif readiness == 1.0:
                reason = f"Available unit within {dist_km} km ({int(capability_match * 100)}% capability alignment)."
            else:
                reason = f"Responder is currently {status.lower()} at {dist_km} km distance; recommended for secondary staging."

            # ETA estimation: ~35 km/h urban emergency response speed
            est_eta_min = max(2.0, round((dist_km / 35.0) * 60.0, 1))
            loc_address = res.get("location", {}).get("address") or f"Sector Command ({category.title()})"

            candidates.append(ResourceRecommendation(
                resource_id=res_id,
                name=res_name,
                category=category,
                distance_km=dist_km,
                capability_match=capability_match,
                readiness=readiness,
                score=final_score,
                reason=reason,
                status=status,
                capacity=capacity,
                eta_min=est_eta_min,
                location_name=loc_address
            ))

        # Sort descending by score
        candidates.sort(key=lambda x: x.score, reverse=True)
        top_recommendations = candidates[:k]

        # Check for Resource Shortage on High/Critical Emergencies
        if (severity in ["CRITICAL", "HIGH"] or priority == "P1") and not any(c.status == "AVAILABLE" for c in top_recommendations):
            from backend.app.websocket.manager import WebSocketEventType
            await ws_manager.broadcast_event(
                WebSocketEventType.RESOURCE_SHORTAGE,
                {
                    "incident_id": incident.get("incident_id", incident_id),
                    "incident_type": inc_type,
                    "severity": severity,
                    "priority": priority,
                    "available_units_found": 0,
                    "alert": f"CRITICAL RESOURCE SHORTAGE: No available matching response units within operational radius for incident {incident.get('incident_id', incident_id)}."
                }
            )

        return IncidentRecommendationsResponse(
            incident_id=incident.get("incident_id", incident_id),
            incident_type=inc_type,
            severity=severity,
            priority=priority,
            recommendations=top_recommendations
        )

    @classmethod
    async def assign_resource_to_incident(
        cls,
        db: AsyncIOMotorDatabase,
        incident_id: str,
        resource_id: str,
        actor: str = "Command Dispatcher",
        notes: Optional[str] = None
    ) -> AssignResourceResponse:
        """
        Assigns/dispatches a resource to an active incident:
        1. Resource status -> BUSY
        2. Resource.current_incident_id -> incident_id
        3. Incident.assigned_resources -> appends resource_id
        4. Incident timeline -> logs dispatch event
        5. WebSocket -> broadcasts RESOURCE_ASSIGNED
        """
        now_utc = datetime.now(timezone.utc)
        from backend.app.websocket.manager import WebSocketEventType
        from bson import ObjectId

        # 1. Fetch Incident
        inc_query = {"incident_id": incident_id}
        if ObjectId.is_valid(incident_id):
            inc_query = {"$or": [{"incident_id": incident_id}, {"_id": ObjectId(incident_id)}]}
        incident = await db.incidents.find_one(inc_query)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found.")

        # 2. Fetch Resource
        res_query = {"resource_id": resource_id}
        if ObjectId.is_valid(resource_id):
            res_query = {"$or": [{"resource_id": resource_id}, {"_id": ObjectId(resource_id)}]}
        resource = await db.resources.find_one(res_query)
        if not resource:
            raise ValueError(f"Resource '{resource_id}' not found.")

        # 3. Update Resource
        await db.resources.update_one(
            res_query,
            {
                "$set": {
                    "status": ResourceStatus.BUSY.value,
                    "current_incident_id": incident.get("incident_id", incident_id),
                    "updated_at": now_utc
                }
            }
        )

        # 4. Update Incident
        timeline_entry = {
            "timestamp": now_utc,
            "action": f"Resource Dispatched: {resource.get('name', resource_id)}",
            "actor": actor,
            "details": notes or f"Assigned {resource.get('category')} unit ({resource_id}) to scene."
        }

        await db.incidents.update_one(
            inc_query,
            {
                "$addToSet": {"assigned_resources": resource.get("resource_id", resource_id)},
                "$set": {
                    "status": "DISPATCHED" if incident.get("status") in ["REPORTED", "VERIFIED"] else incident.get("status"),
                    "updated_at": now_utc
                },
                "$push": {"timeline": timeline_entry}
            }
        )

        updated_inc = await db.incidents.find_one(inc_query)
        assigned_list = updated_inc.get("assigned_resources", [])

        # 5. Broadcast WebSocket Events
        from backend.app.services.realtime import (
            broadcast_resource_dispatched,
            broadcast_resource_available,
            broadcast_incident_updated,
        )

        r_data = {
            "resource_id": resource.get("resource_id", resource_id),
            "name": resource.get("name"),
            "category": resource.get("category"),
            "capabilities": resource.get("capabilities", []),
            "status": "BUSY",
            "current_incident_id": incident.get("incident_id", incident_id),
        }
        await broadcast_resource_dispatched(
            resource_id=resource.get("resource_id", resource_id),
            incident_id=incident.get("incident_id", incident_id),
            resource_data=r_data,
            extra={"assigned_resources": assigned_list, "actor": actor}
        )

        if updated_inc:
            await broadcast_incident_updated(updated_inc)

        return AssignResourceResponse(
            incident_id=incident.get("incident_id", incident_id),
            resource_id=resource.get("resource_id", resource_id),
            resource_name=resource.get("name", "Emergency Responder"),
            assigned_resources=assigned_list,
            message=f"Resource '{resource.get('name')}' ({resource_id}) dispatched to incident {incident_id}."
        )

    @classmethod
    async def release_resource(
        cls,
        db: AsyncIOMotorDatabase,
        resource_id: str,
        actor: str = "Field Commander",
        incident_id: Optional[str] = None
    ) -> ReleaseResourceResponse:
        """
        Release a resource back to pool:
        1. Resource status -> AVAILABLE
        2. Resource.current_incident_id -> null
        3. Incident.assigned_resources -> pulls resource_id if bound to an incident
        4. WebSocket -> broadcasts RESOURCE_AVAILABLE
        """
        now_utc = datetime.now(timezone.utc)
        from backend.app.websocket.manager import WebSocketEventType
        from bson import ObjectId

        res_query = {"resource_id": resource_id}
        if ObjectId.is_valid(resource_id):
            res_query = {"$or": [{"resource_id": resource_id}, {"_id": ObjectId(resource_id)}]}

        resource = await db.resources.find_one(res_query)
        if not resource:
            raise ValueError(f"Resource '{resource_id}' not found.")

        target_inc_id = incident_id or resource.get("current_incident_id")

        await db.resources.update_one(
            res_query,
            {
                "$set": {
                    "status": ResourceStatus.AVAILABLE.value,
                    "current_incident_id": None,
                    "updated_at": now_utc
                }
            }
        )

        updated_inc = None
        if target_inc_id:
            inc_q = {"incident_id": target_inc_id}
            if ObjectId.is_valid(target_inc_id):
                inc_q = {"$or": [{"incident_id": target_inc_id}, {"_id": ObjectId(target_inc_id)}]}
            timeline_entry = {
                "timestamp": now_utc,
                "action": f"Resource Released: {resource.get('name', resource_id)}",
                "actor": actor,
                "details": f"Unit returned to available standby pool."
            }
            await db.incidents.update_one(
                inc_q,
                {
                    "$pull": {"assigned_resources": resource.get("resource_id", resource_id)},
                    "$push": {"timeline": timeline_entry}
                }
            )
            updated_inc = await db.incidents.find_one(inc_q)

        from backend.app.services.realtime import (
            broadcast_resource_available,
            broadcast_incident_updated,
        )

        r_data = {
            "resource_id": resource.get("resource_id", resource_id),
            "name": resource.get("name"),
            "category": resource.get("category"),
            "capabilities": resource.get("capabilities", []),
            "status": "AVAILABLE",
            "current_incident_id": None,
        }
        await broadcast_resource_available(
            resource_id=resource.get("resource_id", resource_id),
            resource_data=r_data,
            previous_incident_id=target_inc_id
        )

        if updated_inc:
            await broadcast_incident_updated(updated_inc)

        return ReleaseResourceResponse(
            resource_id=resource.get("resource_id", resource_id),
            resource_name=resource.get("name", "Emergency Responder"),
            new_status="AVAILABLE",
            message=f"Resource '{resource.get('name')}' ({resource_id}) released and marked AVAILABLE."
        )
