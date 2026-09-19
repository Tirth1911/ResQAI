# ResQAI Production Deployment Guide 🚀

This guide provides step-by-step instructions for deploying the **ResQAI** platform to production:
- **Database**: MongoDB Atlas (Cloud)
- **Backend API & WebSockets**: Render / Railway / Fly.io (FastAPI)
- **Frontend Command Center**: Vercel (Next.js 15)

---

## 1. MongoDB Atlas Setup (Cloud Database)

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a new project (e.g. `ResQAI-Production`) and deploy a free **M0 Cluster**.
3. **Security -> Database Access**:
   - Create a database user (e.g. `resqai_admin`) with **Read and write to any database** privilege.
   - Note the password.
4. **Security -> Network Access**:
   - Add IP Address `0.0.0.0/0` (Allow access from anywhere) so serverless and cloud hosting providers can connect.
5. **Database -> Connect**:
   - Choose **Drivers** (Python 3.11+).
   - Copy the SRV connection string:
     ```
     mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - Target database name: `resqai`.

---

## 2. Backend Deployment (Render / Railway / Fly.io)

### Option A: Render (Web Service)
1. Go to [Render Dashboard](https://dashboard.render.com) and click **New + -> Web Service**.
2. Connect your GitHub repository: `https://github.com/Tirth1911/ResQAI`.
3. Configure the service:
   - **Name**: `resqai-backend`
   - **Environment**: `Python 3` (or `Docker`)
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**:
   Add the following variables under the **Environment** tab:

   | Variable | Value | Description |
   |---|---|---|
   | `MONGODB_URI` | `mongodb+srv://<user>:<pwd>@cluster0.xxx.mongodb.net/?retryWrites=true&w=majority` | MongoDB Atlas Connection String |
   | `MONGODB_DATABASE` | `resqai` | Production database name |
   | `AI_API_KEY` | `sk-...` or empty | Optional LLM API Key (falls back to offline rule provider if omitted) |
   | `AI_MODEL` | `gpt-4o-mini` | AI Model ID |
   | `AI_BASE_URL` | `https://api.openai.com/v1` | AI Provider Base URL |
   | `CORS_ORIGINS` | `https://resqai.vercel.app,http://localhost:3000` | Allowed frontend origins (comma-separated) |
   | `JWT_SECRET_KEY` | `your-secure-random-32-character-secret` | JWT signing secret |

5. Click **Create Web Service**.
6. Once deployed, note your service URL (e.g. `https://resqai-backend.onrender.com`).

---

## 3. Frontend Deployment (Vercel)

1. Go to [Vercel Dashboard](https://vercel.com) and click **Add New... -> Project**.
2. Import your GitHub repository (`Tirth1911/ResQAI`).
3. Configure project settings:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click edit and select `frontend`
4. **Environment Variables**:
   Add the following environment variables:

   | Variable | Value | Description |
   |---|---|---|
   | `NEXT_PUBLIC_API_URL` | `https://resqai-backend.onrender.com/api` | Backend REST API endpoint (must use `https://`) |
   | `NEXT_PUBLIC_WS_URL` | `wss://resqai-backend.onrender.com/ws/dashboard` | Backend WebSocket endpoint (must use `wss://`) |

5. Click **Deploy**.
6. Once deployed, Vercel will give you a public URL (e.g. `https://resqai.vercel.app`).
7. Update `CORS_ORIGINS` in your Backend Render dashboard with the newly generated Vercel domain!

---

## 4. Secure Protocol Requirements in Production

In a cloud production environment:
- **Frontend** is served over HTTPS: `https://resqai.vercel.app`
- **Backend REST API** is accessed over HTTPS: `https://resqai-backend.onrender.com/api`
- **Real-Time WebSocket** MUST use secure WebSockets (**WSS**): `wss://resqai-backend.onrender.com/ws/dashboard`

> **Automatic Upgrade**: ResQAI frontend client automatically upgrades `ws://` to `wss://` when running under HTTPS in production browsers to prevent Mixed Content security blocks.

---

## 5. Seed Remote Database

To seed initial demo responder vehicles and user accounts into your production MongoDB Atlas instance:
```bash
# Set your production URI in local terminal:
export MONGODB_URI="mongodb+srv://<username>:<password>@cluster0.xxx.mongodb.net/?retryWrites=true&w=majority"
export MONGODB_DATABASE="resqai"

# Run database seeder:
python -m backend.app.scripts.seed_data
```

---

## 6. End-to-End Production Verification Checklist

Run through this test checklist to confirm all links in the deployment chain:

- [ ] **Frontend → Backend**: Visiting `https://resqai.vercel.app/incidents` fetches the incident list from `https://resqai-backend.onrender.com/api/incidents`.
- [ ] **Backend → MongoDB Atlas**: Submitting a new incident on `/incidents` successfully creates a document in your MongoDB Atlas `resqai.incidents` collection.
- [ ] **Frontend → WebSocket (WSS)**: Top navigation bar shows `CONNECTED (LIVE)` badge; trigger a simulation event on `/simulation` and verify live toast alert appears.
- [ ] **Backend → AI Engine**: Creating an incident without manual type/severity triggers AI analysis and returns classified priority.
