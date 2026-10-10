# SpecterRed X - developer convenience targets.
# Windows users without `make`: run the commands shown under each target.

PY := backend/.venv/Scripts/python.exe

.PHONY: help backend-install backend test eval frontend-install frontend build lint typecheck

help:
	@echo "Targets: backend-install backend test eval frontend-install frontend build lint typecheck"

backend-install:
	cd backend && python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt

backend:
	cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	cd backend && .venv/Scripts/python.exe -m pytest -q

eval:
	cd backend && PYTHONPATH=. .venv/Scripts/python.exe eval.py

frontend-install:
	cd frontend && npm install

frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

lint:
	cd frontend && npm run lint

typecheck:
	cd frontend && npm run typecheck
