# ResQAI 🚨
> **Intelligent Emergency Response & Resource Coordination Platform**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js_15-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB_Atlas-47A248?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ResQAI is a real-time, unified emergency management and dispatch coordination platform. Engineered for emergency operations centers (EOCs), 911 dispatchers, and first responders, ResQAI combines **AI-assisted incident triage**, **adaptive 3-signal duplicate detection**, **geospatial multi-criteria resource matching**, and **sub-second WebSocket synchronization** to accelerate emergency response times and eliminate dispatch fragmentation.

---

## ⚠️ Important Medical & Emergency Dispatch Disclaimer

> **DISCLAIMER**: ResQAI is an intelligent decision-support system designed to assist human dispatchers and emergency operations coordinators. AI-generated incident classifications, severity scores, and dispatch recommendations are **decision-support suggestions** and **must never replace the judgment, protocols, or operational decisions of trained emergency personnel, medical professionals, or incident commanders.**

---

## 📌 Table of Contents
1. [Problem Statement](#-problem-statement)
2. [Problem Background](#-problem-background)
3. [The ResQAI Solution](#-the-resqai-solution)
4. [Key Features](#-key-features)
5. [System Architecture](#-system-architecture)
6. [Technology Stack](#-technology-stack)
7. [MongoDB Architecture](#-mongodb-architecture)
8. [AI Architecture & Offline Fallback](#-ai-architecture--offline-fallback)
9. [Adaptive 3-Signal Duplicate Detection](#-adaptive-3-signal-duplicate-detection)
10. [Multi-Criteria Resource Recommendation Algorithm](#-multi-criteria-resource-recommendation-algorithm)
11. [Real-Time WebSocket Architecture](#-real-time-websocket-architecture)
12. [Screenshots](#-screenshots)
13. [Demo Video](#-demo-video)
14. [Live Deployment](#-live-deployment)
15. [Installation & Setup](#-installation--setup)
    - [Prerequisites](#prerequisites)
    - [Environment Variables](#environment-variables)
    - [MongoDB Setup & Indexing](#mongodb-setup--indexing)
    - [Database Seeding](#database-seeding)
    - [Backend Setup](#backend-setup)
    - [Frontend Setup](#frontend-setup)
16. [Running the Project](#-running-the-project)
17. [API Documentation](#-api-documentation)
18. [3-Minute Demo Instructions](#-3-minute-demo-instructions)
19. [Team Members](#-team-members)
20. [Future Scope](#-future-scope)

---

## ❗ Problem Statement
During major emergencies (urban fires, multi-vehicle expressway collisions, industrial chemical spills, floods), emergency call centers experience an immediate flood of chaotic, unstructured reports from citizens, IoT alarms, and radio feeds. 

Dispatchers face critical bottlenecks:
- **Triage Delay**: High cognitive overhead in reading raw text descriptions, determining incident urgency, and formulating immediate Standard Operating Procedures (SOPs).
- **Duplicate Overload & Alert Fatigue**: Dozens of citizens calling about the same incident create duplicate tickets, fragmenting responder visibility and wasting precious dispatch capacity.
- **Suboptimal Fleet Routing**: Dispatchers lack dynamic matching that factors in vehicle travel distance, specialized onboard capabilities, and crew readiness.
- **Fragmented Situational Awareness**: Lack of instant, bi-directional telemetry synchronization across dispatchers, hospital trauma bays, and field teams.

---

## 📖 Problem Background
In high-density metropolitan and industrial corridors (such as Ahmedabad-Sanand GIDC, Bengaluru Tech Corridor, Mumbai Expressways), emergency response latency is often measured in minutes that dictate casualty survival rates. When an incident occurs:
- 70% of inbound calls within the first 15 minutes describe the same incident using varying citizen vocabulary.
- Manual cross-referencing of street intersections delays unit deployment by 4 to 8 minutes.
- Dispatching units without checking required capabilities (e.g. sending a standard patrol car to a chemical fire requiring hydraulic extrication or foam suppression) causes secondary dispatch delays.

---

## 💡 The ResQAI Solution
ResQAI transforms emergency command operations into an automated, data-driven workflow:
1. **Instant AI Triage**: Ingests citizen/IoT text and outputs structured severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), priority (`P1`-`P4`), and immediate SOP checklists.
2. **Deterministic Offline Fallback**: Zero-dependency local heuristic engine ensures 100% triage uptime even if third-party LLM APIs fail.
3. **Adaptive 3-Signal Deduplication**: Spatio-temporal and NLP cosine similarity automatically flags and merges duplicate reports into a unified master timeline.
4. **Weighted Multi-Criteria Resource Matching**: Scores response units based on proximity (50%), capability match (30%), and fleet readiness (20%).
5. **Real-Time WebSocket Bus**: Synchronizes all cartographic map markers, active incident queues, and KPI analytics instantly across all connected screens.

---

## ✨ Key Features

- 🚨 **Centralized Emergency Command Dashboard**: Unified triage feed with live incident metrics, quick actions, and status badges.
- 📋 **Incident Management (`/incidents`)**: Filter by severity, priority, status, source, and search keywords with full audit timelines.
- 🚑 **Fleet & Resource Coordination (`/resources`)**: Real-time status tracker (`AVAILABLE`, `BUSY`, `EN_ROUTE`, `MAINTENANCE`) and instant one-click assignment/release.
- 🗺 **Interactive Map Cartography (`/map`)**: Full-screen geospatial map with custom responder and incident markers powered by Leaflet.
- 📊 **Real-Time KPI Analytics (`/analytics`)**: MongoDB aggregation dashboards for response time SLA compliance, severity breakdowns, and hotspot analytics.
- 🧪 **Disaster Scenario Simulator (`/simulation`)**: Multi-step simulation engine supporting 5 realistic crisis scenarios with duplicate burst injection.
- ⏱ **Dedicated 3-Minute Judge Demo (`/demo`)**: 13-step automated interactive walkthrough of the entire emergency lifecycle.
- 🔒 **Lightweight Role-Based Access Control (`/login`)**: JWT authentication with 5 pre-configured roles (`ADMIN`, `DISPATCHER`, `FIELD_TEAM`, `HOSPITAL`, `VIEWER`).

---

## 🏗 System Architecture

```
[ Citizen Calls / IoT Sensors / Field Teams ]
                     │
                     ▼
    ┌──────────────────────────────────┐
    │     FastAPI Gateway (:8000)      │
    │  - Pydantic v2 Schema Validation │
    │  - JWT Bearer Authentication     │
    │  - Sanitized Error Handling      │
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

## 🛠 Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Async Database Driver**: Motor (AsyncIOMotorClient)
- **Validation**: Pydantic v2 / Pydantic-Settings
- **Real-Time Gateway**: WebSockets (native async broadcast bus)
- **Security & Auth**: PyJWT, Passlib with Bcrypt

### Frontend
- **Framework**: Next.js 15 (App Router, Turbopack)
- **Language**: TypeScript & React 19
- **Styling**: Tailwind CSS & Lucide React
- **Geospatial UI**: Leaflet & React-Leaflet (OpenStreetMap)
- **Visualizations**: Recharts data visualization library

### Database & Storage
- **Database**: **MongoDB ONLY** (Atlas or local instance) with GeoJSON `Point` coordinates and `2dsphere` spatial indexing.

---

## 🗄 MongoDB Architecture

ResQAI is built natively and exclusively on MongoDB. All entities leverage flexible BSON documents and spatial indexing:

### Key Collections & Indexes
1. **`incidents`**: Emergency incident records with GeoJSON coordinates.
   - Index: `{"location": "2dsphere"}`
   - Index: `{"status": 1, "reported_at": -1}`
   - Index: `{"incident_id": 1}` (unique)
2. **`resources`**: Response fleet units (fire engines, ambulances, rescue boats, hazmat).
   - Index: `{"location": "2dsphere"}`
   - Index: `{"status": 1, "category": 1}`
   - Index: `{"resource_id": 1}` (unique)
3. **`hospitals`**: Trauma centers and emergency room bed capacities.
   - Index: `{"location": "2dsphere"}`
4. **`users`**: Dispatchers and command personnel.
   - Index: `{"email": 1}` (unique), `{"user_id": 1}` (unique)
5. **`notifications`**: Real-time alerts and escalation logs.
   - Index: `{"created_at": -1, "read": 1}`

---

## 🧠 AI Architecture & Offline Fallback

ResQAI employs a resilient multi-tier intelligence pipeline:
- **Primary AI Triage**: Analyzes caller descriptions using LLMs (Gemini / OpenAI API compatible) to extract incident taxonomy (`fire`, `flood`, `road_accident`, `medical_emergency`, `gas_leak`, `industrial_hazard`, `building_collapse`, `earthquake`), severity, and priority.
- **Immediate Action Generator**: Generates actionable, step-by-step Standard Operating Procedures (e.g. chemical containment, cordon perimeter, triage bay designation).
- **Deterministic Offline Rule Provider**: If external API keys are omitted or network connectivity is severed, a local heuristic engine evaluates keyword vector matrices to guarantee **100% zero-downtime triage**.

---

## 🔍 Adaptive 3-Signal Duplicate Detection

To prevent call center paralysis during mass disaster events, ResQAI evaluates 3 concurrent signals for every incoming report:

$$\text{Confidence} = (w_1 \cdot S_{\text{geo}}) + (w_2 \cdot S_{\text{time}}) + (w_3 \cdot S_{\text{nlp}})$$

1. **Geographic Proximity ($S_{\text{geo}}$)**: Haversine distance between coordinates. Distance $\le 1.0\text{ km}$ triggers proximity match. High-density weighting applied within $250\text{ m}$.
2. **Temporal Window ($S_{\text{time}}$)**: Delta between report timestamps. Incidents within a $45\text{-minute}$ rolling window are considered active candidates.
3. **NLP Semantic Text Similarity ($S_{\text{nlp}}$)**: Custom lightweight tokenizer with stop-word elimination and suffix stemming computing TF-IDF cosine similarity.

**Automatic Merge**: When confidence exceeds $80\%$, the incoming report is automatically merged into the master incident, updating citizen call tallies and timeline logs without creating duplicate tickets.

---

## 🎯 Multi-Criteria Resource Recommendation Algorithm

ResQAI ranks emergency response units dynamically using a multi-criteria scoring algorithm:

$$\text{Final Score} = (S_{\text{distance}} \times 0.50) + (S_{\text{capability}} \times 0.30) + (S_{\text{readiness}} \times 0.20)$$

- **Distance Score ($S_{\text{distance}}$)**: Linear decay based on travel distance: $\max(0.0, 1.0 - \frac{\text{dist\_km}}{50.0})$.
- **Capability Match ($S_{\text{capability}}$)**: Validates category and onboard equipment (e.g. `HYDRAULIC_CUTTERS`, `ICU_TRANSPORT`, `HAZMAT_SUITS`, `SCBA`, `LIFE_JACKETS`).
- **Readiness ($S_{\text{readiness}}$)**: Operational status (`AVAILABLE` = 1.0, `EN_ROUTE` = 0.5, `BUSY` = 0.0).

---

## ⚡ Real-Time WebSocket Architecture

ResQAI connects frontend interfaces directly to the backend event bus via `/ws/dashboard`:
- **Broadcast Events**: `INCIDENT_CREATED`, `INCIDENT_UPDATED`, `INCIDENT_CLASSIFIED`, `INCIDENT_DUPLICATED`, `RESOURCE_ASSIGNED`, `RESOURCE_RELEASED`, `INCIDENT_ESCALATED`, `RESOURCE_SHORTAGE`, `NOTIFICATION_CREATED`.
- **Client Synchronization**: React hook `useRealtimeEvents` updates UI state, markers, and metrics instantaneously without full page reloads.

---

## 📸 Screenshots

| Incident Management (`/incidents`) | Spatial Cartography (`/map`) |
|:---:|:---:|
| ![Incident Management](docs/images/incidents.png) | ![Live Map](docs/images/map.png) |

| Analytics Dashboard (`/analytics`) | Dedicated Judge Demo (`/demo`) |
|:---:|:---:|
| ![Analytics](docs/images/analytics.png) | ![Demo Mode](docs/images/demo.png) |

*(Screenshots can be added to `docs/images/`)*

---

## 🎥 Demo Video
- **Walkthrough Video**: [Watch ResQAI Demo on YouTube](https://youtube.com) *(Add link to hackathon submission recording)*

---

## 🌐 Live Deployment
- **Production Deployment Guide**: [docs/deployment_guide.md](docs/deployment_guide.md)
- **Frontend Dashboard**: [https://resqai-demo.vercel.app](https://resqai-demo.vercel.app) *(Or local: http://localhost:3000)*
- **Backend API Gateway**: [http://localhost:8000/api](http://localhost:8000/api)
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MongoDB (Local instance on `localhost:27017` or MongoDB Atlas URI)

### Environment Variables
Copy `.env.example` to `.env` in the root folder:
```bash
cp .env.example .env
```

Key configuration options:
```env
# MongoDB Datastore
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=resqai

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Optional AI API Key (Falls back to offline rule provider if empty)
AI_API_KEY=
AI_MODEL=gpt-4o-mini

# Frontend Public Endpoints
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/dashboard
```

### MongoDB Setup & Indexing
ResQAI automatically verifies and builds all 8 MongoDB collections and `2dsphere` spatial indexes upon backend startup.

### Database Seeding
Seed demo users, response fleet vehicles, and hospitals:
```bash
python -m backend.app.scripts.seed_data
```

### Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🚀 Running the Project

Once both servers are running:
1. Open your browser to **[http://localhost:3000](http://localhost:3000)**.
2. Sign in via `/login` (use the one-click **DISPATCHER** demo button).
3. Access the Live Dashboard at `/dashboard`.

---

## 📖 API Documentation

Interactive API documentation is generated automatically by FastAPI:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Detailed endpoint documentation is available in [docs/api.md](docs/api.md).

---

## ⏱ 3-Minute Demo Instructions

To evaluate the complete platform in under 3 minutes:
1. Navigate to **[http://localhost:3000/demo](http://localhost:3000/demo)**.
2. Click **"Start Complete 3-Minute Demo"**.
3. Watch ResQAI execute the 13-step emergency lifecycle:
   - Ingests critical road accident report.
   - AI classifies severity (`CRITICAL`) and priority (`P1`).
   - Recommends nearest hydraulic extrication and ambulance units.
   - Ingests secondary citizen report and detects duplicate via 3-Signal NLP/Geo match.
   - Merges duplicate into master timeline and broadcasts WebSocket updates.
   - Resolves incident and refreshes real-time analytics aggregation.

For the complete guide, see [docs/demo.md](docs/demo.md).

---

## 👥 Team Members

- **Tirth Patel** — *Full-Stack Architecture, AI Triage & Backend Engineering*
- **Contributors** — *ResQAI Open Source Community*

---

## 🔮 Future Scope

- 🛰 **Satellite SAR Imagery Integration**: Ingesting high-resolution synthetic aperture radar for flood inundation mapping.
- 📱 **Offline P2P Mesh Network Relay**: Enabling first responders in disconnected disaster zones to sync telemetry over local Bluetooth/LoRa mesh.
- 🚁 **Autonomous Drone Telemetry Ingestion**: Automated thermal imaging stream analysis for survivors trapped in multi-story building fires.
- 🌐 **Multilingual Voice-to-Text Triage**: Real-time translation and transcription for regional citizen emergency hotlines.
