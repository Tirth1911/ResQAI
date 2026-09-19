import logging
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timezone, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.config import settings
from backend.app.services.geo import haversine

logger = logging.getLogger("resqai.dedup")

DEDUP_DISTANCE_KM = getattr(settings, "DEDUP_DISTANCE_THRESHOLD_KM", 1.0)
DEDUP_WINDOW_MIN = getattr(settings, "DEDUP_TIME_WINDOW_MINUTES", 45)
DEDUP_SIM_THRESHOLD = getattr(settings, "DEDUP_SIM_THRESHOLD", 0.25)


def compute_text_similarity(new_text: str, candidate_texts: List[str]) -> float:
    """Compute TF-IDF cosine similarity between new report text and combined candidate texts."""
    cand_combined = " ".join(candidate_texts).strip()
    new_text_clean = (new_text or "").strip()

    if not new_text_clean or not cand_combined:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([new_text_clean, cand_combined])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(sim)
    except Exception as e:
        logger.debug(f"TF-IDF vectorizer fallback: {e}")
        # Word set Jaccard fallback
        s1 = set(new_text_clean.lower().split())
        s2 = set(cand_combined.lower().split())
        if not s1 or not s2:
            return 0.0
        return float(len(s1.intersection(s2)) / len(s1.union(s2)))


async def find_duplicate(
    db: Any,
    new_report: Dict[str, Any],
    triage_result: Any
) -> Optional[Tuple[Dict[str, Any], float]]:
    """
    Find existing duplicate incident using spatial MongoDB $near query,
    haversine distance, temporal window, incident type compatibility, and TF-IDF text similarity.
    """
    lat = float(new_report.get("lat", 0.0))
    lng = float(new_report.get("lng", 0.0))

    report_time = new_report.get("reported_at") or datetime.now(timezone.utc)
    if report_time.tzinfo is None:
        report_time = report_time.replace(tzinfo=timezone.utc)

    time_threshold = report_time - timedelta(minutes=DEDUP_WINDOW_MIN)

    # 1. MongoDB Candidate Selection Query ($near on 2dsphere index)
    query = {
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": DEDUP_DISTANCE_KM * 1000.0
            }
        },
        "status": {"$nin": ["resolved", "RESOLVED", "closed", "CLOSED"]},
        "updated_at": {"$gte": time_threshold}
    }

    try:
        cursor = db.incidents.find(query).limit(20)
        candidates = await cursor.to_list(length=20)
    except Exception as err:
        logger.warning(f"Spatial $near query error (fallback to standard query): {err}")
        # Fallback if 2dsphere index not available yet in test DB
        fallback_query = {
            "status": {"$nin": ["resolved", "RESOLVED", "closed", "CLOSED"]},
            "updated_at": {"$gte": time_threshold}
        }
        cursor = db.incidents.find(fallback_query).limit(50)
        candidates = await cursor.to_list(length=50)

    best_candidate = None
    best_score = 0.0

    new_type = getattr(triage_result, "type", "other") if not isinstance(triage_result, dict) else triage_result.get("type", "other")
    new_text = new_report.get("normalized_text") or new_report.get("text", "")

    for cand in candidates:
        cand_loc = cand.get("location", {})
        cand_coords = cand_loc.get("coordinates", [0.0, 0.0]) if isinstance(cand_loc, dict) else [0.0, 0.0]
        cand_lng, cand_lat = cand_coords[0], cand_coords[1]

        # Condition 1: Haversine distance <= DEDUP_DISTANCE_KM
        dist = haversine(lat, lng, cand_lat, cand_lng)
        if dist > DEDUP_DISTANCE_KM:
            continue

        # Condition 2: Time difference <= DEDUP_WINDOW_MIN minutes
        reports_list = cand.get("reports", [])
        if reports_list and isinstance(reports_list, list):
            latest_report = reports_list[-1]
            cand_time = latest_report.get("reported_at") or cand.get("updated_at") or cand.get("reported_at")
        else:
            cand_time = cand.get("updated_at") or cand.get("reported_at") or datetime.now(timezone.utc)

        if cand_time and cand_time.tzinfo is None:
            cand_time = cand_time.replace(tzinfo=timezone.utc)

        dt_min = abs((report_time - cand_time).total_seconds()) / 60.0
        if dt_min > DEDUP_WINDOW_MIN:
            continue

        # Condition 4: Text similarity >= adaptive threshold based on distance
        cand_texts = []
        if reports_list:
            for r in reports_list:
                cand_texts.append(r.get("normalized_text") or r.get("text", ""))
        else:
            cand_texts.append(cand.get("description", ""))

        sim = compute_text_similarity(new_text, cand_texts)

        # Condition 3: Same incident type or compatible emergency taxonomy
        cand_type = str(cand.get("type", "other")).lower()
        norm_new_type = str(new_type).lower()

        COMPATIBLE_TYPES = [
            {"fire", "industrial_hazard", "gas_leak", "other"},
            {"medical_emergency", "road_accident", "other"},
            {"flood", "building_collapse", "earthquake", "other"}
        ]

        type_match = (cand_type == norm_new_type) or (cand_type == "other") or (norm_new_type == "other")
        if not type_match:
            for group in COMPATIBLE_TYPES:
                if cand_type in group and norm_new_type in group:
                    type_match = True
                    break

        if not type_match and sim < 0.30:
            continue

        # Adaptive similarity threshold: closer distance requires lower text similarity
        if dist <= 0.2:
            min_sim = 0.05
        elif dist <= 0.5:
            min_sim = 0.10
        else:
            min_sim = DEDUP_SIM_THRESHOLD

        if sim < min_sim:
            continue

        # Combined Score Formula
        dist_factor = max(0.0, 1.0 - (dist / DEDUP_DISTANCE_KM))
        time_factor = max(0.0, 1.0 - (dt_min / DEDUP_WINDOW_MIN))
        combined_score = 0.4 * dist_factor + 0.3 * time_factor + 0.3 * max(sim, min_sim)

        if combined_score > best_score:
            best_score = combined_score
            best_candidate = cand

    if best_candidate and best_score > 0.0:
        return best_candidate, round(best_score, 4)

    return None
