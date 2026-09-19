# ResQAI API & Intelligence Documentation

Base URLs:
- `/api/incidents`
- `/api/v1/incidents`

Interactive OpenAPI Docs: `http://localhost:8000/docs`

---

## 🔍 Duplicate Incident Detection Engine

ResQAI evaluates incoming reports across **3 concurrent signals** to prevent alert fatigue and redundant dispatches:

1. **Geographic Distance**: $\le 1.0\text{ km}$ (via MongoDB 2dsphere index & Haversine formula)
2. **Temporal Window**: $\le 45\text{ minutes}$ from active incident reporting time
3. **Description Similarity**: $\ge 0.80$ (via lightweight Stemmed TF-IDF & Cosine Similarity)

### Duplicate Check Endpoint: `POST /api/incidents/check-duplicate`

**Request:**
```json
{
  "title": "Industrial chemical warehouse fire and explosion",
  "description": "Distillation plant exploded with heavy black smoke at GIDC Vatva block 4 gate 2.",
  "location": {
    "latitude": 23.0235,
    "longitude": 72.5734
  },
  "source": "citizen"
}
```

**Response (`200 OK`):**
```json
{
  "is_duplicate": true,
  "matched_incident_id": "INC-1001",
  "confidence": 0.94,
  "distance_km": 0.35,
  "time_diff_minutes": 5.0,
  "text_similarity": 0.98,
  "explanation": "Duplicate detected: Report is 0.35 km from active incident 'INC-1001' (Major Industrial Chemical Fire in GIDC Vatva), submitted 5.0 minutes apart with 98% text similarity."
}
```

---

## 📋 Complete Incident, AI & Deduplication Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/incidents` | Ingest incident report (auto-deduplicates & merges when `auto_dedup=true`) |
| `POST` | `/api/incidents/check-duplicate` | **Check if report is a duplicate** (3-signal evaluation) |
| `GET` | `/api/incidents/{incident_id}/related` | **Get merged duplicate calls**, timeline logs, and nearby active incidents |
| `POST` | `/api/incidents/{incident_id}/analyze` | **Trigger AI Intelligence Engine** (type, severity, priority, SOP recommendations) |
| `GET` | `/api/incidents` | Paginated incident list with filtering |
| `GET` | `/api/incidents/active` | Unresolved active incidents (`REPORTED`, `VERIFIED`, `DISPATCHED`, `IN_PROGRESS`) |
| `GET` | `/api/incidents/critical` | High-urgency incidents (`CRITICAL` severity or `P1` priority) |
| `GET` | `/api/incidents/nearby` | 2dsphere geospatial search by `longitude`, `latitude`, `max_distance_meters` |
| `GET` | `/api/incidents/stats` | Real-time incident statistical aggregates |
| `GET` | `/api/incidents/{incident_id}` | Get incident details by `INC-YYYYMMDD-XXXX` or MongoDB `_id` |
| `PATCH` | `/api/incidents/{incident_id}` | Update incident attributes, coordinates, or assign resources |
| `DELETE` | `/api/incidents/{incident_id}` | Delete incident record |
| `POST` | `/api/incidents/{incident_id}/verify` | Transition status to `VERIFIED` |
| `POST` | `/api/incidents/{incident_id}/resolve` | Transition status to `RESOLVED` |
| `POST` | `/api/incidents/{incident_id}/close` | Transition status to `CLOSED` |
