.PHONY: backend frontend seed simulate reset help

VENV_PYTHON = ./venv/Scripts/python.exe

backend:
	$(VENV_PYTHON) -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev

seed:
	$(VENV_PYTHON) -m backend.app.scripts.seed_data

reset:
	$(VENV_PYTHON) -m backend.app.scripts.seed_data --reset

simulate:
	$(VENV_PYTHON) scripts/simulate_stream.py --scenario factory_fire --speed 2.0
