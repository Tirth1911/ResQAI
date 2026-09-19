# ResQAI API Specification 📡

Base URL: `http://localhost:8000/api` (or `http://localhost:8000/api/v1`)  
Interactive Swagger Docs: `http://localhost:8000/docs`  
Interactive ReDoc: `http://localhost:8000/redoc`

---

## 1. Authentication Endpoints (`/api/auth`)

### `POST /api/auth/login`
Authenticate with email and password.
- **Request Body**:
  ```json
  {
    "email": "dispatcher@resqai.org",
    "password": "ResQAI@2026!"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "expires_in_minutes": 1440,
    "user": {
      "user_id": "USR-DISP-002",
      "email": "dispatcher@resqai.org",
      "full_name": "Captain Marcus Vance",
      "role": "DISPATCHER"
    }
  }
  ```

### `POST /api/auth/quick-login`
One-click role login for demo evaluation.
- **Request Body**:
  ```json
  {
    "role": "DISPATCHER"
  }
  ```

### `GET /api/auth/me`
Retrieve current authenticated user profile (Requires `Authorization: Bearer <token>`).

---

## 2. Incidents Endpoints (`/api/incidents`)

### `POST /api/incidents`
Create an emergency report. Automatically checks for duplicates in spatial/temporal proximity.
- **Query Parameters**: `auto_dedup=true`
- **Request Body**:
  ```json
  {
    "title": "Chemical Factory Fire",
    "description": "Explosion in warehouse storage with toxic black smoke and 4 trapped staff.",
    "source": "CITIZEN_CALL",
    "location": {
      "latitude": 12.9252,
      "longitude": 77.6742,
      "address": "Sector 4 Industrial Zone"
    }
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "incident_id": "INC-20260919-0012",
    "title": "Chemical Factory Fire",
    "type": "fire",
    "severity": "CRITICAL",
    "priority": "P1",
    "status": "REPORTED",
    "confidence": 0.96,
    "location": {
      "type": "Point",
      "coordinates": [77.6742, 12.9252]
    }
  }
  ```

### `GET /api/incidents`
List incidents with filtering and pagination.
- **Query Parameters**: `status`, `severity`, `priority`, `type`, `source`, `search`, `page`, `limit`

### `GET /api/incidents/{incident_id}`
Retrieve complete incident details, timeline events, assigned units, and related duplicate reports.

### `POST /api/incidents/{incident_id}/analyze`
Trigger AI classification and SOP generation.

### `POST /api/incidents/check-duplicate`
Evaluate if an incoming report matches an active incident using 3-signal deduplication.

---

## 3. Resources Endpoints (`/api/resources`)

### `GET /api/resources`
List fleet response units with category, status, and capability filters.

### `GET /api/resources/recommend/{incident_id}`
Calculate ranked responder recommendations for an incident using multi-criteria weighted scoring.
- **Response**:
  ```json
  {
    "incident_id": "INC-20260919-0012",
    "recommendations": [
      {
        "resource_id": "RES-FIR-01",
        "name": "Heavy Hydraulic Fire Engine 01",
        "category": "FIRE_TRUCK",
        "distance_km": 1.2,
        "capability_match": 1.0,
        "readiness": 1.0,
        "score": 0.945,
        "reason": "1.2km away | Matches FIRE_TRUCK capabilities | Unit AVAILABLE"
      }
    ]
  }
  ```

### `POST /api/resources/assign`
Assign an emergency resource to an active incident.

### `POST /api/resources/release/{resource_id}`
Release a resource back to the available standby fleet.

---

## 4. Analytics Endpoints (`/api/analytics`)

- `GET /api/analytics/overview` — High-level KPI summary (total, active, critical, resolved, response time, utilization).
- `GET /api/analytics/incidents-by-type` — Categorical breakdown.
- `GET /api/analytics/incidents-by-severity` — Severity distribution (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- `GET /api/analytics/response-times` — SLA compliance benchmarks.
- `GET /api/analytics/resource-utilization` — Fleet usage telemetry.
- `GET /api/analytics/trends` — 7-day incident timeline trends.
- `GET /api/analytics/hotspots` — Top recurring spatial emergency sectors.

---

## 5. Simulation & Demo Endpoints (`/api/simulation`)

- `POST /api/simulation/start` — Start disaster scenario simulation sequence.
- `POST /api/simulation/stop` — Immediately halt simulation.
- `POST /api/simulation/reset` — Reset state and release fleet units.
- `GET /api/simulation/status` — Current simulation playback telemetry.
- `POST /api/simulation/demo/setup` — Reset and prepare a clean state for judge evaluation.
- `POST /api/simulation/demo/step/{step_number}` — Execute one of the 13 dedicated demo steps.

---

## 6. Real-Time WebSocket Gateway (`/ws/dashboard`)

- **URL**: `ws://localhost:8000/ws/dashboard`
- **Initial Connection Handshake**:
  ```json
  {
    "event": "CONNECTED",
    "data": { "message": "Connected to ResQAI Real-time Emergency Event Bus" }
  }
  ```
- **Streamed Event Frame**:
  ```json
  {
    "event": "RESOURCE_ASSIGNED",
    "data": {
      "incident_id": "INC-20260919-0012",
      "resource_id": "RES-FIR-01",
      "resource_name": "Heavy Hydraulic Fire Engine 01"
    }
  }
  ```
