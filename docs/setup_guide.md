# ResQAI Setup & Execution Guide

This guide details how to run the ResQAI platform locally.

---

## Prerequisites

- **Python**: 3.10+
- **Node.js**: 18+ (Node 20+ recommended)
- **MongoDB**: Local MongoDB instance (`mongodb://localhost:27017`) or **MongoDB Atlas** URI.

---

## 1. Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

If using **MongoDB Atlas**, update `MONGODB_URL` in `.env`:
```env
MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.mongodb.net/resqai?retryWrites=true&w=majority
```

---

## 2. Backend Setup (FastAPI)

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. (Optional) Seed emergency units into MongoDB:
   ```bash
   python scripts/seed_data.py
   ```

4. Start FastAPI server:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   - API Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/api/v1/health`

---

## 3. Frontend Setup (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already installed):
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

   - Open `http://localhost:3000` in your browser.

---

## 4. Run with Docker Compose (All-in-One)

```bash
docker-compose up --build
```
