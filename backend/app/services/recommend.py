import logging
from typing import Dict, Any, List, Optional
from backend.app.services.geo import haversine

logger = logging.getLogger("resqai.recommend")

PRIMARY_RESPONDERS = {
    "fire": ["fire_truck", "fire", "disaster_response_team"],
    "medical_emergency": ["ambulance", "medical_team"],
    "road_accident": ["ambulance", "police", "police_unit"],
    "flood": ["rescue_team", "disaster_response_team"],
    "industrial_hazard": ["fire_truck", "disaster_response_team", "gas_leak"],
    "building_collapse": ["rescue_team", "fire_truck"],
    "gas_leak": ["fire_truck", "disaster_response_team"],
    "earthquake": ["rescue_team", "ambulance", "disaster_response_team"],
    "other": ["ambulance", "fire_truck", "police", "rescue_team"]
}

SEVERITY_REQUIRED_UNITS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 5
}


def normalize_kind(kind_str: str) -> str:
    k = (kind_str or "").lower().strip()
    if "fire" in k:
        return "fire_truck"
    elif "amb" in k or "med" in k:
        return "ambulance"
    elif "police" in k or "cop" in k:
        return "police_unit"
    elif "rescue" in k:
        return "rescue_team"
    elif "disaster" in k:
        return "disaster_response_team"
    return k or "unit"


async def recommend_resources_for_incident(
    db: Any,
    incident: Dict[str, Any]
) -> Dict[str, Any]:
    """Recommend optimal response units, hospital, and relief camp for an incident."""
    inc_type = str(incident.get("type", "other")).lower()
    severity = str(incident.get("severity", "medium")).lower()

    loc = incident.get("location", {})
    coords = loc.get("coordinates", [0.0, 0.0]) if isinstance(loc, dict) else [0.0, 0.0]
    lng, lat = float(coords[0]), float(coords[1])

    required_count = SEVERITY_REQUIRED_UNITS.get(severity, 2)
    primaries = PRIMARY_RESPONDERS.get(inc_type, ["ambulance", "fire_truck", "police", "rescue_team"])

    # 1. Candidate selection using $geoNear aggregation
    candidates = []
    try:
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [lng, lat]},
                    "distanceField": "distance_m",
                    "spherical": True,
                    "maxDistance": 50000,
                    "query": {
                        "status": {"$in": ["available", "AVAILABLE"]}
                    }
                }
            }
        ]
        cursor = db.resources.aggregate(pipeline)
        candidates = await cursor.to_list(length=100)
    except Exception as err:
        logger.warning(f"GeoNear aggregation fallback to standard fetch: {err}")
        cursor = db.resources.find({"status": {"$in": ["available", "AVAILABLE"]}})
        candidates = await cursor.to_list(length=100)

    units_scored = []
    for r in candidates:
        r_id = str(r.get("_id"))
        r_code = r.get("resource_id", r_id)

        # Distance calculation
        if "distance_m" in r:
            distance_km = float(r["distance_m"]) / 1000.0
        else:
            r_loc = r.get("location", {})
            r_coords = r_loc.get("coordinates", [lng, lat]) if isinstance(r_loc, dict) else [lng, lat]
            r_lng, r_lat = float(r_coords[0]), float(r_coords[1])
            distance_km = haversine(lat, lng, r_lat, r_lng)

        r_kind = r.get("kind") or r.get("category") or r.get("type") or "unit"
        norm_r_kind = normalize_kind(r_kind)

        # Capability & Primaries Matching
        is_primary = any(p in norm_r_kind for p in primaries) or norm_r_kind in primaries
        r_capabilities = [c.lower() for c in r.get("capabilities", [])]
        has_capability = any(inc_type in c or c in inc_type for c in r_capabilities)

        if is_primary:
            capability_match = 1.0
            reason_type = f"primary responder for {inc_type}"
        elif has_capability:
            capability_match = 0.6
            reason_type = f"capable unit for {inc_type}"
        else:
            capability_match = 0.5
            reason_type = f"available backup unit"

        distance_score = max(0.0, 1.0 - (distance_km / 25.0))
        readiness = 1.0  # Available units only

        # Score formula: 0.5*distance_score + 0.3*capability_match + 0.2*readiness
        score = round(0.5 * distance_score + 0.3 * capability_match + 0.2 * readiness, 3)

        # ETA = distance / 40 km/h * 60 + 2 min mobilization
        eta_min = round((distance_km / 40.0) * 60.0 + 2.0, 1)

        reason = f"{distance_km:.1f} km away, ETA {int(eta_min)} min, {reason_type}"

        units_scored.append({
            "resource_id": r_code,
            "id": r_id,
            "name": r.get("name") or r.get("resource_name") or r_code,
            "kind": r_kind,
            "normalized_kind": norm_r_kind,
            "score": score,
            "distance_km": round(distance_km, 2),
            "eta_min": eta_min,
            "reason": reason,
            "raw_resource": r
        })

    # Sort candidates by score descending, then distance ascending
    units_scored.sort(key=lambda u: (-u["score"], u["distance_km"]))

    # 2. Select recommendations matching required kinds
    recommended_units = units_scored[:10]

    # Check shortage
    shortage = len(recommended_units) < required_count
    shortage_detail = None
    if shortage:
        shortage_detail = f"Required {required_count} units for {severity} severity incident, but only {len(recommended_units)} available."

    # 3. Hospital recommendation
    hospital_rec = None
    try:
        h_cursor = db.hospitals.aggregate([
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [lng, lat]},
                    "distanceField": "distance_m",
                    "spherical": True,
                    "maxDistance": 100000,
                    "query": {"status": {"$in": ["available", "AVAILABLE"]}}
                }
            },
            {"$limit": 1}
        ])
        h_docs = await h_cursor.to_list(length=1)
        if h_docs:
            h = h_docs[0]
            dist_km = round(float(h.get("distance_m", 0)) / 1000.0, 2)
            hospital_rec = {
                "hospital_id": h.get("hospital_id") or str(h.get("_id")),
                "name": h.get("name", "Nearest Hospital"),
                "distance_km": dist_km,
                "available_beds": h.get("available_beds", h.get("capacity", 10)),
                "address": h.get("address", "")
            }
    except Exception as err:
        logger.debug(f"Hospital query fallback: {err}")
        h_doc = await db.hospitals.find_one({"status": {"$in": ["available", "AVAILABLE"]}})
        if h_doc:
            h_loc = h_doc.get("location", {})
            h_coords = h_loc.get("coordinates", [lng, lat]) if isinstance(h_loc, dict) else [lng, lat]
            dist_km = round(haversine(lat, lng, float(h_coords[1]), float(h_coords[0])), 2)
            hospital_rec = {
                "hospital_id": h_doc.get("hospital_id") or str(h_doc.get("_id")),
                "name": h_doc.get("name", "Nearest Hospital"),
                "distance_km": dist_km,
                "available_beds": h_doc.get("available_beds", 10),
                "address": h_doc.get("address", "")
            }

    # 4. Relief camp recommendation for flood or critical
    relief_camp_rec = None
    if inc_type in ["flood", "earthquake"] or severity == "critical":
        relief_camp_rec = {
            "camp_id": "CAMP-CENTRAL-01",
            "name": "Central Emergency Relief Camp & Shelter",
            "capacity": 500,
            "status": "active",
            "distance_km": 3.5
        }

    formatted_units = []
    for u in recommended_units:
        unit_copy = dict(u)
        unit_copy.pop("raw_resource", None)
        formatted_units.append(unit_copy)

    return {
        "units": formatted_units,
        "hospital": hospital_rec,
        "relief_camp": relief_camp_rec,
        "shortage": shortage,
        "shortage_detail": shortage_detail
    }
