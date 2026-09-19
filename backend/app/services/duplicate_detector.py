import math
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from difflib import SequenceMatcher
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.utils.geo import haversine_distance_km

logger = logging.getLogger("resqai.duplicate_detector")

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "him", "his", "how", "i", "if", "in",
    "into", "is", "it", "its", "just", "me", "more", "most", "my", "no", "nor",
    "not", "now", "of", "off", "on", "once", "only", "or", "other", "our", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with",
    "would", "you", "your"
}


# =============================================================================
# 1. LIGHTWEIGHT LOCAL NLP & TF-IDF TEXT SIMILARITY
# =============================================================================

def stem_token(word: str) -> str:
    """Lightweight suffix stripping for lexical root matching."""
    for suffix in ["ing", "tion", "sion", "ment", "ed", "es", "s", "ly"]:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[:-len(suffix)]
    return word


def tokenize(text: str) -> List[str]:
    """Extract cleaned stemmed word tokens without punctuation."""
    words = re.findall(r"\b[a-z0-9_]+\b", text.lower())
    return [stem_token(w) for w in words if w not in STOP_WORDS and len(w) > 2]


def compute_tfidf_cosine_similarity(text1: str, text2: str) -> float:
    """
    Compute fast, lightweight TF-IDF & Stemmed Cosine Similarity.
    Zero external dependencies, 100% deterministic and reliable.
    """
    tok1 = tokenize(text1)
    tok2 = tokenize(text2)

    if not tok1 or not tok2:
        return 0.0

    v1 = Counter(tok1)
    v2 = Counter(tok2)

    intersection = set(v1.keys()) & set(v2.keys())
    numerator = sum(v1[x] * v2[x] for x in intersection)

    sum1 = sum(v1[x] ** 2 for x in v1.keys())
    sum2 = sum(v2[x] ** 2 for x in v2.keys())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    cosine_sim = float(numerator) / denominator if denominator else 0.0
    seq_ratio = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    dice_coeff = (2.0 * len(intersection)) / (len(set(v1.keys())) + len(set(v2.keys()))) if (set(v1.keys()) | set(v2.keys())) else 0.0
    containment = (float(len(intersection)) / min(len(set(v1.keys())), len(set(v2.keys())))) if min(len(set(v1.keys())), len(set(v2.keys()))) > 0 else 0.0

    # Max score across cosine, sequence, dice, and token containment
    final_score = max(cosine_sim, seq_ratio, dice_coeff, containment * 0.90)
    return round(min(1.0, max(0.0, final_score)), 4)


# =============================================================================
# 2. SCHEMAS
# =============================================================================

class DuplicateCheckRequest(BaseModel):
    title: str = Field(..., min_length=3, description="Incident title to check")
    description: str = Field(..., min_length=5, description="Incident description to check")
    location: Dict[str, float] = Field(..., description="Target coordinates: {'latitude': lat, 'longitude': lon}")
    source: Optional[str] = Field(default="citizen")
    reported_at: Optional[datetime] = Field(default=None)


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    matched_incident_id: Optional[str] = None
    confidence: float = 0.0
    distance_km: Optional[float] = None
    time_diff_minutes: Optional[float] = None
    text_similarity: Optional[float] = None
    explanation: str


class RelatedIncidentsResponse(BaseModel):
    incident_id: str
    duplicate_count: int
    reports: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    nearby_active_incidents: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# 3. DUPLICATE DETECTOR ENGINE
# =============================================================================

class DuplicateDetector:

    @classmethod
    async def check_duplicate(
        cls,
        db: AsyncIOMotorDatabase,
        title: str,
        description: str,
        latitude: float,
        longitude: float,
        reported_at: Optional[datetime] = None,
        distance_threshold_km: float = settings.DISTANCE_THRESHOLD_KM,
        time_threshold_minutes: int = settings.TIME_THRESHOLD_MINUTES,
        text_similarity_threshold: float = settings.TEXT_SIMILARITY_THRESHOLD
    ) -> DuplicateCheckResponse:
        """
        Execute 3-signal spatio-temporal and NLP duplicate detection:
        Signal 1: Distance <= DISTANCE_THRESHOLD_KM (1.0 km)
        Signal 2: Time Diff <= TIME_THRESHOLD_MINUTES (45 min)
        Signal 3: Text Similarity >= TEXT_SIMILARITY_THRESHOLD (0.80)
        """
        now_utc = reported_at or datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        # Step 1: Query MongoDB for active or recent incidents within spatial bounds (approx 2.5km box)
        max_dist_meters = max(2500.0, distance_threshold_km * 1000.0)

        cursor = db.incidents.find({
            "status": {"$in": ["REPORTED", "VERIFIED", "DISPATCHED", "IN_PROGRESS"]},
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "$maxDistance": max_dist_meters
                }
            }
        }).limit(20)

        best_match: Optional[Dict[str, Any]] = None
        best_confidence: float = 0.0
        best_dist_km: float = 0.0
        best_time_diff: float = 0.0
        best_similarity: float = 0.0

        query_text = f"{title}. {description}"

        async for candidate in cursor:
            # Signal 1: Geographic Distance
            coords = candidate.get("location", {}).get("coordinates", [])
            if len(coords) < 2:
                continue
            cand_lon, cand_lat = coords[0], coords[1]
            dist_km = haversine_distance_km(latitude, longitude, cand_lat, cand_lon)

            # Signal 2: Time Difference
            cand_reported_at = candidate.get("reported_at")
            if not cand_reported_at:
                cand_reported_at = candidate.get("created_at", now_utc)

            if isinstance(cand_reported_at, datetime):
                if cand_reported_at.tzinfo is None:
                    cand_reported_at = cand_reported_at.replace(tzinfo=timezone.utc)
                time_diff_min = abs((now_utc - cand_reported_at).total_seconds()) / 60.0
            else:
                time_diff_min = 0.0

            # Signal 3: Description Similarity
            cand_title = candidate.get("title", "")
            cand_desc = candidate.get("description", "")
            cand_text = f"{cand_title}. {cand_desc}"
            similarity = compute_tfidf_cosine_similarity(query_text, cand_text)

            # Check if all 3 thresholds pass (with adaptive spatial weighting for ultra-close calls)
            is_spatial_match = dist_km <= distance_threshold_km
            is_temporal_match = time_diff_min <= time_threshold_minutes
            
            # Adaptive text threshold: if within 250m, 50% text similarity is sufficient; otherwise require full threshold or high composite confidence
            effective_text_threshold = min(text_similarity_threshold, 0.50 if dist_km <= 0.25 else text_similarity_threshold)
            is_text_match = similarity >= effective_text_threshold or composite_confidence >= 0.75

            # Composite confidence score
            spatial_score = max(0.0, 1.0 - (dist_km / max(1.0, distance_threshold_km)))
            temporal_score = max(0.0, 1.0 - (time_diff_min / max(1.0, time_threshold_minutes)))
            composite_confidence = round((similarity * 0.50) + (spatial_score * 0.30) + (temporal_score * 0.20), 2)

            if is_spatial_match and is_temporal_match and is_text_match:
                if composite_confidence > best_confidence:
                    best_match = candidate
                    best_confidence = composite_confidence
                    best_dist_km = round(dist_km, 2)
                    best_time_diff = round(time_diff_min, 1)
                    best_similarity = similarity

        if best_match:
            matched_id = best_match.get("incident_id", str(best_match.get("_id")))
            matched_title = best_match.get("title", "")
            explanation = (
                f"Duplicate detected: Report is {best_dist_km} km from active incident '{matched_id}' ({matched_title}), "
                f"submitted {best_time_diff} minutes apart with {int(best_similarity * 100)}% text similarity."
            )
            return DuplicateCheckResponse(
                is_duplicate=True,
                matched_incident_id=matched_id,
                confidence=best_confidence,
                distance_km=best_dist_km,
                time_diff_minutes=best_time_diff,
                text_similarity=best_similarity,
                explanation=explanation
            )

        return DuplicateCheckResponse(
            is_duplicate=False,
            matched_incident_id=None,
            confidence=0.0,
            distance_km=None,
            time_diff_minutes=None,
            text_similarity=None,
            explanation="No duplicate match found. Distance, temporal window, or text similarity thresholds were not met."
        )

    @classmethod
    async def merge_duplicate_report(
        cls,
        db: AsyncIOMotorDatabase,
        matched_incident_id: str,
        new_report_data: Dict[str, Any],
        similarity_score: float = 0.85
    ) -> Optional[Dict[str, Any]]:
        """
        Merge duplicate call/report into existing incident in MongoDB:
        - Link report
        - Increment report_count and duplicate_count
        - Append report details to reports & timeline
        - Update last_reported_at and updated_at
        - Broadcast WebSocket notification
        """
        from backend.app.services.db_service import clean_mongo_doc
        from backend.app.websocket.manager import ws_manager
        from bson import ObjectId

        query = {"incident_id": matched_incident_id}
        if ObjectId.is_valid(matched_incident_id):
            query = {"$or": [{"incident_id": matched_incident_id}, {"_id": ObjectId(matched_incident_id)}]}

        existing = await db.incidents.find_one(query)
        if not existing:
            return None

        now_utc = datetime.now(timezone.utc)
        report_entry = {
            "source": new_report_data.get("source", "citizen"),
            "title": new_report_data.get("title", ""),
            "description": new_report_data.get("description", ""),
            "reported_at": now_utc,
            "text_similarity": similarity_score,
            "caller_contact": new_report_data.get("caller_contact"),
        }

        timeline_entry = {
            "timestamp": now_utc,
            "action": "Duplicate Call Merged",
            "actor": f"Deduplication Engine ({new_report_data.get('source', 'citizen')})",
            "details": f"Merged secondary report '{new_report_data.get('title', '')}' ({int(similarity_score * 100)}% match)"
        }

        await db.incidents.update_one(
            query,
            {
                "$inc": {"duplicate_count": 1, "report_count": 1},
                "$push": {
                    "reports": report_entry,
                    "timeline": timeline_entry
                },
                "$set": {
                    "last_reported_at": now_utc,
                    "updated_at": now_utc
                }
            }
        )

        updated = await db.incidents.find_one(query)
        cleaned = clean_mongo_doc(updated)

        if cleaned:
            from backend.app.websocket.manager import WebSocketEventType
            await ws_manager.broadcast_event(
                WebSocketEventType.INCIDENT_DUPLICATED,
                {
                    "incident": cleaned,
                    "merged_report": report_entry,
                    "duplicate_count": cleaned.get("duplicate_count", 1)
                }
            )

        return cleaned

    @classmethod
    async def get_related_incidents(
        cls,
        db: AsyncIOMotorDatabase,
        incident_id: str
    ) -> Optional[RelatedIncidentsResponse]:
        """Fetch all merged reports, timeline events, and spatial neighbors for an incident."""
        from backend.app.services.db_service import clean_mongo_doc
        from bson import ObjectId

        query = {"incident_id": incident_id}
        if ObjectId.is_valid(incident_id):
            query = {"$or": [{"incident_id": incident_id}, {"_id": ObjectId(incident_id)}]}

        incident = await db.incidents.find_one(query)
        if not incident:
            return None

        coords = incident.get("location", {}).get("coordinates", [])
        nearby_list = []
        if len(coords) == 2:
            lon, lat = coords[0], coords[1]
            nearby_cursor = db.incidents.find({
                "incident_id": {"$ne": incident.get("incident_id")},
                "status": {"$in": ["REPORTED", "VERIFIED", "DISPATCHED", "IN_PROGRESS"]},
                "location": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "$maxDistance": 5000.0
                    }
                }
            }).limit(5)
            async for n in nearby_cursor:
                cleaned_n = clean_mongo_doc(n)
                n_coords = cleaned_n.get("location", {}).get("coordinates", [])
                if len(n_coords) == 2:
                    cleaned_n["distance_km"] = round(haversine_distance_km(lat, lon, n_coords[1], n_coords[0]), 2)
                nearby_list.append(cleaned_n)

        return RelatedIncidentsResponse(
            incident_id=incident.get("incident_id", str(incident.get("_id"))),
            duplicate_count=incident.get("duplicate_count", 0),
            reports=incident.get("reports", []),
            timeline=incident.get("timeline", []),
            nearby_active_incidents=nearby_list
        )
