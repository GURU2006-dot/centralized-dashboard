# SIH 26016 — What we have done so far

**Problem:** National Land Acquisition Management & Intelligence Platform  
**Problem statement:** 26016 (Smart India Hackathon 2026)  
**Date of this pack:** 2026-09-08  
**Status:** Architecture frozen + **Phase 1 (database foundation) complete**  
**Not started:** FastAPI routers, React UI, ML training, authentication UI, live government APIs

All prototype data is **SYNTHETIC**. It is not live land records, cadastral maps, or government statistics.

---

## 1. Timeline of work

| Step | What happened |
|---|---|
| 1 | Spec analysed (SIH 26016 requirements R7–R12 + extras) |
| 2 | Full architecture pack written (`docs/`) — **no application code** |
| 3 | Architecture review: **APPROVED** with 5 corrections |
| 4 | Architecture **frozen** (`docs/architecture-freeze.md`) |
| 5 | **Phase 1 only** implemented: PostgreSQL/PostGIS, SQLAlchemy models, Alembic, seed, reset, tests |

---

## 2. Architecture pack (`docs/`)

These documents are the frozen design for later phases. They are **not** fully implemented yet except the database.

| File | Contents |
|---|---|
| `docs/README.md` | Index of all artifacts |
| `docs/00-analysis.md` | Spec analysis, requirement map, assumptions |
| `docs/A-repository-structure.md` | Target monorepo tree |
| `docs/B-database-erd.md` | Entities, FKs, indexes, Mermaid ERD |
| `docs/C-api-contracts.md` | Target REST contracts (implement later by P0/P1/P2) |
| `docs/D-frontend-component-hierarchy.md` | React page/component tree (not built) |
| `docs/E-ml-interface.md` | Random Forest delay-risk contract (not trained yet) |
| `docs/F-integration-interfaces.md` | Mock adapter design (not coded yet) |
| `docs/G-auth-rbac.md` | JWT + role matrix (not coded yet) |
| `docs/H-implementation-plan.md` | Tasks T0–T18 |
| `docs/I-one-day-execution-plan.md` | 10-hour SIH clock |
| `docs/J-architecture-decisions.md` | ADRs |
| `docs/architecture-freeze.md` | Five review corrections |

### Frozen corrections (must be followed in every later phase)

1. **Proposal approval is the only approval action.** `proposals.status` = APPROVED/REJECTED. Acquisition cases are created *after* approval and then follow the case workflow. No second approve/reject on cases.
2. Full API spec is the **target**, not a mandate to build every endpoint now. P0 first.
3. `risk_score` is a **model risk score**, not a calibrated probability of delay. Always show the synthetic-model disclaimer.
4. Do **not** put owner ID numbers, phones, or addresses in general parcel API responses.
5. Government systems stay behind adapters. Prototype = **MOCK only**. No invented URLs or credentials.

---

## 3. Phase 1 — what is implemented (code)

### 3.1 Runtime / ops

- `docker-compose.yml` — PostgreSQL **16** + PostGIS (`postgis/postgis:16-3.4`), user/db `nlamp`
- `.env.example` — `DATABASE_URL=postgresql+psycopg://nlamp:nlamp@localhost:5432/nlamp`
- `README.md` — commands to start DB, migrate, seed, reset, test

### 3.2 SQLAlchemy 2.0 models (`backend/app/models/`)

Tables:

`roles`, `users`, `states`, `districts`, `workflow_stage_definitions`, `projects`, `land_parcels`, `owners`, `parcel_owners`, `proposals`, `proposal_parcels`, `acquisition_cases`, `workflow_events`, `documents`, `compensation`, `affected_families`, `rehabilitation`, `resettlement`, `possession`, `field_verifications`, `notifications`, `alerts`, `ml_predictions`, `audit_logs`

Notable constraints:

- `data_source ∈ {SYNTHETIC, MOCK_ADAPTER, EXTERNAL}` (seed always `SYNTHETIC`)
- Unique `(project_id, parcel_id)` on `acquisition_cases`
- PostGIS `geometry(MultiPolygon,4326)` + `geography(Point,4326)` on parcels, plus GeoJSON JSONB fallback
- **Append-only trigger** on `workflow_events` (UPDATE/DELETE raise)

### 3.3 Workflow (correction #1)

**Proposal (authoritative approval):**  
`DRAFT → SUBMITTED → UNDER_VERIFICATION → APPROVED | REJECTED`

**Acquisition case (only after APPROVED):**  
`SIA → NOTIFICATION → AWARD → COMPENSATION_ASSESSMENT → COMPENSATION_PAID → POSSESSION → REHABILITATION_RESETTLEMENT → COMPLETED`

There is **no** `APPROVAL` stage on cases.

### 3.4 Alembic

- Revision: `7f0736d5b557_initial_schema`
- Creates PostGIS/pgcrypto extensions, all tables, indexes, CHECKs, append-only trigger

### 3.5 Synthetic seed (`scripts/seed_db.py`)

Approximate counts after seed:

| Entity | Count |
|---|---|
| States | 3 (TG, MH, OD) |
| Districts | 6 |
| Projects | 8 |
| Land parcels | **80** |
| Owners / parcel_owners | 95 / 112 |
| Proposals / proposal_parcels | 8 / 80 |
| Acquisition cases | 60 (approved proposals only) |
| Workflow events | 236 |
| Compensation / families / R&R / possession | 32 / 51 / 17 / 16 |
| Alerts / ML predictions | 12 / 24 |

- ULPINs look like `SYN00000000001` (prefix `SYN` = synthetic, not DoLR)
- Geometries are generated rectangles, also written to `data/geo/parcels.geojson`
- Demo users (password hash of `Demo@1234`, auth UI **not** built):  
  `admin@demo.local`, `officer@demo.local`, `approver@demo.local`, `field@demo.local`

### 3.6 Reset + tests

- `scripts/demo_reset.py` — drop public schema, migrate, reseed
- `backend/tests/test_database.py` — **14 tests passed**, covering:
  - PostGIS enabled
  - all required tables
  - ≥80 synthetic parcels
  - parcel↔owner M:N
  - project↔parcel
  - proposal↔parcel
  - cases only for APPROVED proposals
  - unique (project, parcel)
  - stage catalogue (no APPROVAL stage)
  - append-only workflow events
  - geometry round-trip
  - `data_source` CHECK

---

## 4. What is explicitly **not** in this zip as running software

| Area | Status |
|---|---|
| FastAPI routes (`/api/...`) | Designed in `docs/C-api-contracts.md` only |
| React / Vite / Leaflet / dashboard | Designed in `docs/D-...` only |
| JWT login UI | Designed in `docs/G-...` only |
| Random Forest `train.py` / `model.pkl` | Designed in `docs/E-...` only; seed has example `ml_predictions` rows |
| Mock government adapters | Designed in `docs/F-...` only |
| Live DoLR / BhuNaksha / NGDRS | **Will not** be built in the one-day prototype |

---

## 5. How to use this pack

```bash
# 1. Start PostgreSQL 16 + PostGIS
docker compose up -d db

# 2. Python deps + migrate
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head

# 3. Seed SYNTHETIC data
cd ..
python scripts/seed_db.py

# 4. Tests
cd backend && python -m pytest -q

# Reset anytime
python scripts/demo_reset.py
```

If Docker is unavailable: local PostgreSQL + PostGIS on `localhost:5432`, user/password/database `nlamp`, then the same migrate/seed commands.

---

## 6. Next (when Phase 2 is authorised)

Do **not** start this until asked. Planned next slice from `docs/H-implementation-plan.md` / P0:

- FastAPI health + layered app shell
- Auth/JWT/RBAC
- Parcel search/detail + dashboard KPI APIs
- Still no React until the API P0 slice is accepted — unless the next brief says otherwise

---

## 7. Zip contents (this archive)

```
sih-26016-nlamp-phase1/
├── WHAT_WE_HAVE_DONE.md     ← this file
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docs/                    ← frozen architecture
├── backend/                 ← models, alembic, tests
├── scripts/                 ← seed + demo_reset
└── data/                    ← SYNTHETIC geojson + disclaimers
```

No `.venv`, `__pycache__`, or pip cache is included.
