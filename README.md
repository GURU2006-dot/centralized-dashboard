# SIH 26016 — National Land Acquisition Management & Intelligence Platform

**Current status: Phase 5 complete — READY FOR SIH DEMO** — database + FastAPI JWT/RBAC + workflow + React command center + synthetic delay-risk RF + mock integration adapters, with E2E validation.

Demo: [docs/DEMO-SCRIPT.md](docs/DEMO-SCRIPT.md) · Architecture: [docs/FINAL-ARCHITECTURE.md](docs/FINAL-ARCHITECTURE.md) · Tests: [docs/FINAL-TEST-REPORT.md](docs/FINAL-TEST-REPORT.md) · Phase 5: [docs/PHASE5-REPORT.md](docs/PHASE5-REPORT.md)

All seeded rows are **`data_source = SYNTHETIC`**. They are not live land records, cadastral maps, or government statistics.

Architecture corrections applied:

1. Proposal `status` is the **only** approval action. Acquisition-case stages are the post-approval lifecycle (`SIA` → `COMPLETED`). Cases are created only for `APPROVED` proposals.
2. Full API spec is target architecture; implement by P0/P1/P2.
3. `ml_predictions.risk_score` is a model risk score, not a calibrated probability of delay. `trained_on = SYNTHETIC`.
4. Owner `id_number`, `phone`, and `address` are never returned by parcel APIs.
5. No live government integrations and no invented API credentials.

## Start PostgreSQL / PostGIS

```bash
docker compose up -d db
```

## Migrate + seed

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
cd ..
python scripts/seed_db.py
```

Reset: `python scripts/demo_reset.py`

## Run the API

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Health: `GET /health`
- Swagger: `/docs`
- ReDoc: `/redoc`

Demo logins (password `Demo@1234`): `admin@demo.local`, `officer@demo.local`, `approver@demo.local`, `field@demo.local`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite listens on `0.0.0.0:5173` and proxies `/api` and `/health` to the FastAPI process on port 8000.

## Tests

```bash
cd backend
python -m pytest -q
```

## Local fallback (no Docker)

PostgreSQL 16/17 with PostGIS on `localhost:5432`, user/password/db `nlamp`. Copy `.env.example` to `.env`.

1st : backend : 1.docker desktop start
2. docker compose up -d db
3.cd backend
4..\.venv\Scripts\Activate.ps1
5.uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

2nd : frontend : 1. cd frontend
2.npm run dev