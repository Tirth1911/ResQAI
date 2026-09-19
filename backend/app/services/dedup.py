import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from pymongo.asynchronous.database import AsyncDatabase
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.db import to_geojson
from app.models import IncidentStatus, IncidentType
from app.services.geo import haversine_km
from app.services.triage import TriageResult

logger = logging.getLogger("resqai.dedup")


def compute_text_similarity(text1: str, text2: str) -> float:
    """
    Computes TF-IDF cosine similarity between two texts using scikit-learn.
    Falls back to token Jaccard similarity if vocabulary is empty or only stop words.
    """
    cleaned1 = text1.strip().lower()
    cleaned2 = text2.strip().lower()

    if not cleaned1 or not cleaned2:
        return 0.0

    if cleaned1 == cleaned2:
        return 1.0

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([cleaned1, cleaned2])
        sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        sim = float(sim_matrix[0][0])
        return max(0.0, min(1.0, sim))
    except ValueError:
        # Fallback when vocabulary has only stop words or numbers
        tokens1 = set(cleaned1.split())
        tokens2 = set(cleaned2.split())
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return float(intersection / union) if union > 0 else 0.0


async def find_duplicate(
    db: AsyncDatabase,
    new_report: Any,
    triage_result: TriageResult,
) -> Optional[tuple[dict[str, Any], float]]:
    """
    Find existing active incident matching candidate criteria.
    1. Single MongoDB geospatial query within DEDUP_DISTANCE_KM and DEDUP_WINDOW_MIN.
    2. Strict Python verification:
       - distance <= DEDUP_DISTANCE_KM (haversine source of truth)
       - time difference <= DEDUP_WINDOW_MIN
       - same incident type (or 'other')
       - TF-IDF cosine similarity >= DEDUP_SIM_THRESHOLD
    Returns (best_candidate_doc, combined_score) or None.
    """
    report_lat = float(new_report.lat)
    report_lng = float(new_report.lng)
    report_text = getattr(new_report, "text", "") or ""

    now = datetime.now(timezone.utc)
    report_time = getattr(new_report, "reported_at", None) or now
    if report_time.tzinfo is None:
        report_time = report_time.replace(tzinfo=timezone.utc)

    max_dist_m = settings.DEDUP_DISTANCE_KM * 1000.0
    time_window_start = report_time - timedelta(minutes=settings.DEDUP_WINDOW_MIN)

    # 1. Candidate selection: single MongoDB query on incidents collection
    geo_point = to_geojson(report_lat, report_lng)
    query: dict[str, Any] = {
        "location": {
            "$near": {
                "$geometry": geo_point,
                "$maxDistance": max_dist_m,
            }
        },
        "status": {"$ne": IncidentStatus.RESOLVED},
        "updated_at": {"$gte": time_window_start},
    }

    cursor = db["incidents"].find(query).limit(20)
    candidates = [doc async for doc in cursor]

    if not candidates:
        return None

    best_candidate: Optional[dict[str, Any]] = None
    best_score: float = -1.0

    # 2. Strict Python-side verification for each candidate
    for cand in candidates:
        # Check coordinates & haversine distance
        coords = cand.get("location", {}).get("coordinates", [])
        if len(coords) < 2:
            continue
        cand_lng, cand_lat = float(coords[0]), float(coords[1])
        dist_km = haversine_km(report_lat, report_lng, cand_lat, cand_lng)

        if dist_km > settings.DEDUP_DISTANCE_KM:
            continue

        # Check time difference with latest report on candidate
        reports = cand.get("reports", [])
        latest_ts = None
        for r in reports:
            r_ts = r.get("reported_at")
            if r_ts is not None:
                if r_ts.tzinfo is None:
                    r_ts = r_ts.replace(tzinfo=timezone.utc)
                if latest_ts is None or r_ts > latest_ts:
                    latest_ts = r_ts

        if latest_ts is None:
            cand_up = cand.get("updated_at", now)
            latest_ts = cand_up if cand_up.tzinfo else cand_up.replace(tzinfo=timezone.utc)

        dt_min = abs((report_time - latest_ts).total_seconds()) / 60.0
        if dt_min > settings.DEDUP_WINDOW_MIN:
            continue

        # Check incident type compatibility (allow "other" to match any type)
        cand_type = cand.get("type")
        is_type_match = (
            triage_result.type == cand_type
            or triage_result.type == IncidentType.OTHER
            or cand_type == IncidentType.OTHER
        )
        if not is_type_match:
            continue

        # Check TF-IDF cosine text similarity
        combined_cand_text = " ".join(r.get("raw_text", "") for r in reports)
        if not combined_cand_text.strip():
            combined_cand_text = cand.get("description", "")

        sim = compute_text_similarity(combined_cand_text, report_text)
        if sim < settings.DEDUP_SIM_THRESHOLD:
            continue

        # Calculate combined score: 0.4*(1 - dist/limit) + 0.3*(1 - dt/limit) + 0.3*similarity
        dist_factor = max(0.0, 1.0 - (dist_km / settings.DEDUP_DISTANCE_KM))
        time_factor = max(0.0, 1.0 - (dt_min / settings.DEDUP_WINDOW_MIN))
        combined_score = (0.4 * dist_factor) + (0.3 * time_factor) + (0.3 * sim)

        if combined_score > best_score:
            best_score = combined_score
            best_candidate = cand

    if best_candidate is not None:
        return best_candidate, round(best_score, 4)

    return None
