import logging
from typing import Any, Optional
from pymongo.asynchronous.database import AsyncDatabase

from app.models import (
    IncidentSeverity,
    IncidentType,
    ResourceKind,
    ResourceStatus,
)
from app.schemas import (
    RecommendationItem,
    RecommendationsOut,
    doc_to_resource_out,
)

logger = logging.getLogger("resqai.recommend")

# Primary responders for each incident type
PRIMARY_RESPONDERS: dict[IncidentType, list[ResourceKind]] = {
    IncidentType.FIRE: [ResourceKind.FIRE_TRUCK],
    IncidentType.MEDICAL: [ResourceKind.AMBULANCE],
    IncidentType.ACCIDENT: [ResourceKind.AMBULANCE, ResourceKind.POLICE_UNIT],
    IncidentType.FLOOD: [ResourceKind.RESCUE_TEAM, ResourceKind.DISASTER_RESPONSE_TEAM],
    IncidentType.INDUSTRIAL: [ResourceKind.FIRE_TRUCK, ResourceKind.DISASTER_RESPONSE_TEAM],
    IncidentType.OTHER: [ResourceKind.POLICE_UNIT],
}

# Unit count requirement by severity
REQUIRED_UNITS_BY_SEVERITY: dict[IncidentSeverity, int] = {
    IncidentSeverity.LOW: 1,
    IncidentSeverity.MEDIUM: 2,
    IncidentSeverity.HIGH: 3,
    IncidentSeverity.CRITICAL: 5,
}

# All deployable tactical response unit kinds
TACTICAL_RESOURCE_KINDS = [
    ResourceKind.FIRE_TRUCK,
    ResourceKind.AMBULANCE,
    ResourceKind.POLICE_UNIT,
    ResourceKind.RESCUE_TEAM,
    ResourceKind.DISASTER_RESPONSE_TEAM,
]


async def get_recommendations(
    db: AsyncDatabase,
    incident: dict[str, Any],
) -> RecommendationsOut:
    """
    Computes optimal resource recommendations for an incident using MongoDB $geoNear.
    - Aggregation with $geoNear on available tactical units.
    - Composite scoring: 0.5*dist + 0.3*capability + 0.2*readiness.
    - Enforces diversity (fire truck for fire/industrial, ambulance for medical/accident, police for critical/accident).
    - Checks for nearest available hospital and relief camp.
    - Detects resource shortage against severity requirements.
    """
    near_point = incident["location"]
    inc_type = IncidentType(incident.get("type", IncidentType.OTHER))
    inc_severity = IncidentSeverity(incident.get("severity", IncidentSeverity.MEDIUM))
    units_required = REQUIRED_UNITS_BY_SEVERITY.get(inc_severity, 2)

    # 1. Geospatial Candidate Query on Tactical Units
    pipeline = [
        {
            "$geoNear": {
                "near": near_point,
                "distanceField": "distance_m",
                "spherical": True,
                "maxDistance": 50000,
                "query": {
                    "status": ResourceStatus.AVAILABLE,
                    "kind": {"$in": TACTICAL_RESOURCE_KINDS},
                },
            }
        },
        {"$limit": 50},
    ]

    cursor = await db["resources"].aggregate(pipeline)
    raw_candidates = [doc async for doc in cursor]

    scored_candidates: list[dict[str, Any]] = []

    primary_kinds = PRIMARY_RESPONDERS.get(inc_type, [ResourceKind.POLICE_UNIT])

    for cand in raw_candidates:
        dist_m = float(cand.get("distance_m", 0.0))
        dist_km = dist_m / 1000.0
        kind = cand.get("kind")
        capabilities = cand.get("capabilities", [])

        # Capability Match
        if kind in primary_kinds:
            capability_match = 1.0
            role_desc = f"primary responder for {inc_type.value}"
        elif inc_type in capabilities:
            capability_match = 0.6
            role_desc = f"certified capability for {inc_type.value}"
        else:
            # Exclude if neither primary nor in capabilities
            continue

        # Distance Score: max(0, 1 - distance_km / 25)
        distance_score = max(0.0, 1.0 - (dist_km / 25.0))

        # Readiness Score: 1.0 for available
        readiness = 1.0

        # Composite score
        score = (0.5 * distance_score) + (0.3 * capability_match) + (0.2 * readiness)

        # ETA: 40 km/h avg speed + 2 min mobilization
        eta_min = round((dist_km / 40.0) * 60.0 + 2.0, 1)

        reason = f"{dist_km:.1f} km away, ETA {eta_min:.0f} min, {role_desc}"

        scored_candidates.append({
            "doc": cand,
            "score": round(score, 4),
            "distance_km": round(dist_km, 2),
            "eta_min": eta_min,
            "reason": reason,
            "kind": kind,
        })

    # Sort all scored candidates by score descending
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)

    # 2. Enforce Mixed Kinds Requirement:
    # Always include fire_truck for fire/industrial
    # Always include ambulance for medical/accident
    # Always include police_unit for critical or accident
    required_kinds: list[ResourceKind] = []
    if inc_type in (IncidentType.FIRE, IncidentType.INDUSTRIAL):
        required_kinds.append(ResourceKind.FIRE_TRUCK)
    if inc_type in (IncidentType.MEDICAL, IncidentType.ACCIDENT):
        required_kinds.append(ResourceKind.AMBULANCE)
    if inc_severity == IncidentSeverity.CRITICAL or inc_type == IncidentType.ACCIDENT:
        required_kinds.append(ResourceKind.POLICE_UNIT)

    selected: list[dict[str, Any]] = []
    selected_ids: set[Any] = set()

    # First pass: satisfy required mixed kinds if available
    for req_kind in required_kinds:
        for cand in scored_candidates:
            if cand["kind"] == req_kind and cand["doc"]["_id"] not in selected_ids:
                selected.append(cand)
                selected_ids.add(cand["doc"]["_id"])
                break

    # Second pass: fill remaining quota up to units_required by score
    for cand in scored_candidates:
        if len(selected) >= units_required:
            break
        if cand["doc"]["_id"] not in selected_ids:
            selected.append(cand)
            selected_ids.add(cand["doc"]["_id"])

    # Convert to RecommendationItem list
    unit_recommendations: list[RecommendationItem] = [
        RecommendationItem(
            resource=doc_to_resource_out(item["doc"]),
            score=item["score"],
            distance_km=item["distance_km"],
            eta_min=item["eta_min"],
            reason=item["reason"],
        )
        for item in selected
    ]

    # 3. Nearest Hospital with capacity > 0
    hospital_out = None
    hosp_cursor = await db["resources"].aggregate([
        {
            "$geoNear": {
                "near": near_point,
                "distanceField": "distance_m",
                "spherical": True,
                "maxDistance": 50000,
                "query": {
                    "kind": ResourceKind.HOSPITAL,
                    "capacity": {"$gt": 0},
                    "status": ResourceStatus.AVAILABLE,
                },
            }
        },
        {"$limit": 1},
    ])
    hosp_candidates = [h async for h in hosp_cursor]
    if hosp_candidates:
        hospital_out = doc_to_resource_out(hosp_candidates[0])

    # 4. Nearest Relief Camp for flood or critical severity
    relief_camp_out = None
    if inc_type == IncidentType.FLOOD or inc_severity == IncidentSeverity.CRITICAL:
        camp_cursor = await db["resources"].aggregate([
            {
                "$geoNear": {
                    "near": near_point,
                    "distanceField": "distance_m",
                    "spherical": True,
                    "maxDistance": 50000,
                    "query": {
                        "kind": ResourceKind.RELIEF_CAMP,
                        "capacity": {"$gt": 0},
                        "status": ResourceStatus.AVAILABLE,
                    },
                }
            },
            {"$limit": 1},
        ])
        camp_candidates = [c async for c in camp_cursor]
        if camp_candidates:
            relief_camp_out = doc_to_resource_out(camp_candidates[0])

    # 5. Shortage Detection
    shortage = len(unit_recommendations) < units_required
    shortage_detail = (
        f"Required {units_required} units for {inc_severity.value} {inc_type.value} incident, "
        f"but only {len(unit_recommendations)} available within 50 km."
        if shortage
        else None
    )

    return RecommendationsOut(
        units=unit_recommendations,
        hospital=hospital_out,
        relief_camp=relief_camp_out,
        shortage=shortage,
        shortage_detail=shortage_detail,
    )
