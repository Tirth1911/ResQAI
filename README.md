 ResQAI: Intelligent Emergency Response & Resource Coordination Platform

> **Problem Statement (PS-9):** A real-time, intelligent emergency management platform designed to ingest multi-source disaster reports, detect duplicate citizen calls, automatically triage incident severities using AI, and coordinate nearest-available emergency resources.

## 🚨 Problem & Solution Overview

### The Problem
During disasters and large-scale accidents (fires, flash floods, highway crashes), emergency command centers receive hundreds of fragmented reports from citizen helplines, IoT sensors, and field officers. This causes:
* **Alert Fatigue & Duplication:** Multiple callers report the same scene, resulting in redundant vehicle dispatches.
* **Triage Delays:** Manual review wastes critical minutes evaluating casualty levels and incident urgency.
* **Misallocated Resources:** Dispatchers lack real-time distance and capacity metrics for ambulances, fire engines, and police units.

### The ResQAI Solution
ResQAI provides a centralized command platform that automates the emergency pipeline:
1. **Multi-Channel Ingestion:** Gathers reports from citizens, IoT sensors, and control rooms.
2. **AI-Powered Triage:** Parses raw text to extract category, severity (`Low`, `Medium`, `High`, `Critical`), and required assets.
3. **Spatio-Temporal Deduplication:** Detects overlapping calls within a specific radius and time window, merging them into one master incident.
4. **Smart Dispatch Recommendation:** Ranks the closest, ready-to-deploy response units based on capacity and travel distance.
5. **Live Interactive Map:** Displays dynamic geospatial incident markers, response units, and route tracking via WebSockets.


## 🛠 System Architecture

[Citizen Reports / Sensor Feeds / Helplines]
                     │
                     ▼
         [FastAPI Backend Gateway]
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   [AI Triage Model]    [Deduplication Engine]
  (Category & Severity)   (Spatial & Temporal Merge)
          └──────────┬──────────┘
                     ▼
       [Resource Matching Engine]
     (Nearest Available Responder)
                     │
                     ▼
         [WebSocket Event Bus]
                     │
                     ▼
    [Next.js + Leaflet Command Center UI]

    🧠 Core Features & Algorithms
    1. Spatio-Temporal Duplicate Detection
       To stop redundant unit dispatches, incoming reports are merged into an active incident 
       Similarity: High semantic match on emergency type and description2. Smart Resource RecommendationUnits are ranked for dispatch suitability using a weighted scoring formula 
       
  💻 Tech StackFrontend: Next.js (App Router), React, Tailwind CSS,Lucide React
                        Geospatial & Mapping: Leaflet.js, React-Leaflet, OpenStreetMap
                         Backend: FastAPI (Python 3.10+), Uvicorn, WebSocketsData 
                         Storage: SQLite / PostgreSQLAI / 
                         NLP: LLM APIs (OpenAI / Groq) for structured triage extraction

