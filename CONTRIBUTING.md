# Contributing to ResQAI 🚨

Thank you for your interest in contributing to **ResQAI**! We welcome contributions to improve emergency dispatch coordination, spatial AI algorithms, and command center interfaces.

---

## Code of Conduct
We are committed to providing a welcoming, inclusive, and harassment-free environment. Please treat all contributors and maintainers with respect.

---

## How to Contribute

### 1. Fork & Clone
```bash
git clone https://github.com/Tirth1911/ResQAI.git
cd ResQAI
```

### 2. Set Up Local Environment

#### Backend (Python / FastAPI)
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r backend/requirements.txt
cp .env.example .env
```

#### Frontend (Next.js / TypeScript)
```bash
cd frontend
npm install
cp .env.example .env.local
```

### 3. Running Development Servers
- Backend: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload`
- Frontend: `cd frontend && npm run dev`

### 4. Running Integration Tests
Before creating a pull request, ensure all tests and lint checks pass:
```bash
# Run integration audit
python -m backend.app.scripts.integration_audit

# Run full flow test
python -m backend.app.scripts.flow_test

# Validate frontend build
cd frontend && npm run build
```

---

## Guidelines for Pull Requests

1. **Keep Pull Requests Focused**: Limit changes to a single feature, bug fix, or optimization.
2. **Preserve MongoDB Stack**: ResQAI is architected strictly around MongoDB Motor async drivers with GeoJSON 2dsphere indexing.
3. **No Secrets in Code**: Never commit `.env` files, API keys, MongoDB credentials, or tokens.
4. **Maintain Type Safety**: Use Pydantic models for all backend routes and TypeScript interfaces for frontend services.
5. **Decision Support Disclaimer**: Ensure all AI classification outputs are clearly identified as decision-support suggestions for human emergency dispatchers.

---

## Questions & Discussions
For issues, feature requests, or questions, please open an Issue on the [GitHub Repository](https://github.com/Tirth1911/ResQAI/issues).
