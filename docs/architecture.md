# ResQAI Architecture & System Design 🏗

ResQAI is an intelligent emergency operations platform engineered for real-time disaster triage, duplicate report aggregation, and optimal multi-unit responder dispatch.

---

## 1. High-Level Architecture Diagram

```
[ Citizen Calls / IoT Sensors / Field Units ]
                     │
                     ▼
    ┌──────────────────────────────────┐
    │     FastAPI Gateway (:8000)      │
    │  - Pydantic v2 Request Validation│
    │  - JWT Bearer Authentication     │
    │  - Rate Limiting & CORS Filter   │
    └────────────────┬─────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐   ┌────────────────────────┐
│  AI Triage &     │   │  Adaptive 3-Signal     │
│  Classification  │   │  Deduplication Engine  │
│  - Severity      │   │  - Spatial Proximity   │
│  - Priority      │   │  - Temporal Window     │
│  - SOP Actions   │   │  - TF-IDF Cosine Sim   │
└────────┬─────────┘   └───────────┬────────────┘
         │                         │
         └───────────┬─────────────┘
                     ▼
       ┌───────────────────────────┐
       │   Resource Matcher Engine │
       │   - Distance Score (50%)  │
       │   - Capability Match (30%)│
       │   - Fleet Readiness (20%) │
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │      MongoDB Datastore    │
       │   - GeoJSON 2dsphere      │
       │   - Compound Status Index │
       │   - Motor Async Driver    │
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ WebSocket Event Bus /ws   │
       │  - Broadcast State Changes│
       │  - Real-time Notifications│
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ Next.js 15 Command Center │
       │  - Leaflet Map Cartography│
       │  - Recharts Analytics     │
       │  - Real-time Incident Feed│
       └───────────────────────────┘
```

---

## 2. Core Subsystems

### A. AI Incident Triage & Classification
- **Primary Engine**: Gemini / Structured LLM provider analyzing natural language emergency descriptions to extract incident taxonomy, severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), and dispatch priority (`P1` - `P4`).
- **Deterministic Offline Fallback**: Zero-dependency rule-based lexical engine with keyword weight vectors, ensuring 100% operational availability during network disconnects or API rate limits.
- **Immediate Action Generator**: Generates step-by-step Standard Operating Procedures (SOPs) based on incident taxonomy (e.g. hazmat evacuation perimeter, triage staging area setup).

### B. Adaptive 3-Signal Deduplication Engine
Prevents emergency call centers from being overwhelmed by duplicate citizen reports during mass disaster events:
1. **Spatial Proximity Signal**: Evaluates Euclidean/Haversine distance between incident coordinates. Reports within $1.0\text{ km}$ trigger proximity flags (with high-density weighting within $250\text{ m}$).
2. **Temporal Window Signal**: Compares timestamp deltas. Reports within a $45\text{-minute}$ rolling window are considered related.
3. **Semantic Text Similarity Signal**: Tokenizes and stems caller text, stripping stop words and calculating TF-IDF cosine similarity.

When all 3 signals breach confidence thresholds ($>80\%$), incoming calls are merged into the primary master incident, updating citizen call counts and appending details to the incident timeline without creating fragmented tickets.

### C. Resource Matcher & Fleet Dispatch Engine
Ranks available emergency responders (ambulances, fire engines, hazmat teams, rescue boats, police units) using a weighted multi-criteria decision algorithm:

$$\text{Match Score} = (\text{Distance Score} \times 0.50) + (\text{Capability Match} \times 0.30) + (\text{Readiness Score} \times 0.20)$$

- **Distance Score**: Decays with distance from incident coordinates: $\max(0.0, 1.0 - \frac{\text{dist}}{50.0})$.
- **Capability Match**: Evaluates category fit and specialized onboard gear (e.g., hydraulic extrication cutters, ICU ventilators, chemical suits).
- **Readiness Score**: Quantifies responder readiness (`AVAILABLE` = 1.0, `EN_ROUTE` = 0.5, `BUSY` = 0.0).

### D. MongoDB Spatial Datastore
- Engineered strictly on MongoDB with native GeoJSON `Point` coordinates: `{"type": "Point", "coordinates": [longitude, latitude]}`.
- Indexes:
  - `location: "2dsphere"` on `incidents`, `resources`, `hospitals`
  - `status: 1, reported_at: -1` compound index on `incidents`
  - `email: 1, user_id: 1` unique indexes on `users`

### E. Real-Time Telemetry & WebSocket Event Bus
- Centralized asynchronous connection manager (`ws_manager`) streaming structured event frames to `/ws/dashboard`.
- Events: `INCIDENT_CREATED`, `INCIDENT_UPDATED`, `INCIDENT_CLASSIFIED`, `RESOURCE_ASSIGNED`, `RESOURCE_RELEASED`, `INCIDENT_ESCALATED`, `RESOURCE_SHORTAGE`, `NOTIFICATION_CREATED`.
- Automatic heartbeat and seamless reconnect handling on the Next.js client (`useRealtimeEvents`).
