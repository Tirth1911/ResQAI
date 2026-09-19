# ResQAI: Intelligent Emergency Response & Resource Coordination Platform

> ResQAI is an AI-powered, real-time emergency dispatch and resource coordination command platform that ingests multi-source disaster reports, clusters and deduplicates redundant citizen calls using spatio-temporal intelligence, triages incidents automatically, and optimizes the allocation of nearest-available response assets across Gujarat's emergency grid.

---

## 🚨 Problem

During disasters and municipal emergencies (fires, floods, multi-vehicle crashes, industrial hazards), emergency response networks and 911/112 dispatch centers face severe challenges:
- **Redundant Call Floods & Alert Fatigue:** Dozens of witnesses call in the same incident, causing fragmented data and duplicate vehicle dispatches.
- **Triage Bottlenecks:** Human operators must manually interpret caller reports under extreme stress, delaying medical or fire intervention.
- **Suboptimal Resource Allocation:** Lack of real-time spatial awareness and capacity tracking leads to inappropriate unit deployment and increased casualty risks.

---

## ✨ Feature List (Overview)

- [ ] **Multi-Source Report Ingestion:** Ingest from citizen apps, hotline calls, IoT flood/smoke sensors, and field officers.
- [ ] **AI-Powered Incident Triage:** Extract incident severity, classification, casualty count, and recommended response kinds (with deterministic rule-based fallback).
- [ ] **Spatio-Temporal Deduplication:** Geo-hash clustering and cosine similarity to merge redundant caller reports into single master incidents.
- [ ] **Smart Dispatch Recommendation Engine:** Multi-factor scoring (distance, resource kind match, ETA, status) to recommend optimal response units.
- [ ] **Live Interactive GIS Command Center:** Leaflet-based real-time tactical map with live responder tracking, incident heatmaps, and routing.
- [ ] **Realtime Event Bus:** Native FastAPI WebSockets broadcasting incident, resource, alert, and assignment events instantly.
- [ ] **Automated Escalation & Alerts:** Proactive detection of delayed responses, resource shortages, and severity escalations.

---

## 💻 Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, PyMongo Async API (`AsyncMongoClient`), Uvicorn, Scikit-Learn, NumPy, HTTPX, Pytest
- **Database:** MongoDB (Local Docker or MongoDB Atlas), GeoJSON with 2dsphere spatial indexing
- **Frontend:** Next.js (App Router, TypeScript), Tailwind CSS, React-Leaflet, Recharts, Lucide React, Zustand
- **AI/LLM:** Groq / OpenAI-compatible API with deterministic rule-based fallbacks
- **Realtime:** Native WebSockets (`/ws`)

---

## 🚀 Setup & Installation

*(Detailed instructions will be expanded as build steps progress)*

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MongoDB 7.0+ (or Docker)

### Quick Start
1. **Clone & Configure Environment:**
   ```bash
   cp .env.example .env
   ```
2. **Start Database (Docker option):**
   ```bash
   docker compose up -d
   ```
3. **Run Backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
4. **Run Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 👥 Team

- Lead Engineer: ResQAI Engineering Team

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
