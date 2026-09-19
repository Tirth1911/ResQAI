# ResQAI Dedicated 3-Minute Demo Guide ⏱

This guide outlines how hackathon judges and evaluators can experience the full end-to-end capabilities of **ResQAI** in under 3 minutes.

---

## 1. Quick Launch

1. Start Backend: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload`
2. Start Frontend: `cd frontend && npm run dev`
3. Navigate in your browser to: **[http://localhost:3000/demo](http://localhost:3000/demo)**

*(Alternatively, login via `/login` using the one-click `DISPATCHER` quick-login button).*

---

## 2. The 13-Step Automated Emergency Lifecycle Walkthrough

On the `/demo` page, click **"Start Complete 3-Minute Demo"** (or use the step-by-step controller) to watch ResQAI execute the complete crisis workflow:

| Step # | Stage Name | Visual UI Action & System Behavior |
|:---:|---|---|
| **Step 1** | **Active Incident Overview** | Renders command center dashboard with active city incidents and live telemetry feeds. |
| **Step 2** | **Ingest Critical Road Accident** | Ingests a high-impact multi-vehicle collision report on the expressway corridor. |
| **Step 3** | **AI Triage & Classification** | AI classifies incident as `road_accident`, assigning `CRITICAL` severity and `P1` priority. |
| **Step 4** | **SOP & Action Generation** | Generates executive situational summary and immediate emergency action checklists. |
| **Step 5** | **Optimal Resource Scoring** | Ranks nearest available ambulance, highway patrol, and hydraulic extrication units. |
| **Step 6** | **Dispatch Responders** | Dispatches top-ranked units; their status transitions to `BUSY` in MongoDB. |
| **Step 7** | **Map Updates** | Spatial cartography markers update with unit locations and dispatched routes. |
| **Step 8** | **Second Citizen Call Ingested** | Simulates a secondary citizen report from the scene with phrasing differences. |
| **Step 9** | **3-Signal Duplicate Detection** | Proximity (<1km), temporal (<45m), and NLP similarity (>80%) flags incoming call as duplicate. |
| **Step 10** | **Automatic Report Merge** | Secondary report merges cleanly into parent incident timeline without dispatching redundant fleet. |
| **Step 11** | **Broadcast Alert Notification** | Triggers in-app command alert and streams event across connected WebSocket clients. |
| **Step 12** | **Resolve Incident** | Incident marked `RESOLVED`; responders released back to `AVAILABLE` standby pool. |
| **Step 13** | **Real-Time Analytics Refresh** | Aggregation metrics update resolution rates, response time averages, and fleet utilization. |

---

## 3. Key Differentiators to Highlight to Judges

- **Zero Hardcoding**: All data flows through live FastAPI endpoints and MongoDB aggregation pipelines.
- **Deduplication Prevents Alert Fatigue**: Demonstrates measurable reduction in duplicate dispatch clutter.
- **Offline Resilience**: Deterministic rule-based fallback guarantees triage even if external AI APIs are unreachable.
- **Sub-Second Real-Time Updates**: WebSocket bus updates map markers, incident queues, and KPI tiles without manual page reloads.
