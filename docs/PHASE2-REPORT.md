# SIH 26016 — Phase 2 Report

**Problem:** National Land Acquisition Management & Intelligence Platform (PS 26016)  
**Step:** FastAPI backend foundation + JWT + RBAC + core REST APIs  
**Date:** 2026-09-08  
**Status:** **Complete.** Phase 3 (workflow mutations) has **not** been started.

All API data is **synthetic demonstration data**. It is not live land records, cadastral maps, or government statistics.

---

## 1. What this step was for

Phase 1 already had PostgreSQL/PostGIS, models, migrations, and seed data.

Phase 2 added a **small, reliable API layer** so a future React app can:

- log in with JWT
- respect roles
- read dashboard / projects / parcels / acquisitions from the real database

It did **not** add React, proposal approval actions, workflow transitions, ML training, or government adapters.

---

## 2. What was delivered

### Application

| Check | Result |
|---|---|
| FastAPI starts | Yes |
| `GET /health` → `{"status":"ok"}` | Yes |
| Swagger `/docs` | Yes (HTTP 200) |
| ReDoc `/redoc` | Yes (HTTP 200) |
| PostgreSQL on startup | Connectivity check logged and succeeded |

### Authentication (JWT)

| Check | Result |
|---|---|
| `POST /api/auth/login` | Issues Bearer token |
| `GET /api/auth/me` | Returns current user (no password/hash) |
| Demo users | All four work with password `Demo@1234` |
| Bad password / unknown user | HTTP 401 |
| Missing / invalid / expired token | HTTP 401 |
| Disabled account | HTTP 403 `ACCOUNT_DISABLED` |

**Demo accounts**

| Email | Role | Scope |
|---|---|---|
| `admin@demo.local` | ADMIN | National |
| `officer@demo.local` | ACQUISITION_OFFICER | Telangana (`TG`) |
| `approver@demo.local` | APPROVING_AUTHORITY | National |
| `field@demo.local` | FIELD_OFFICER | Assigned parcels (TG-RR) |

The Phase 1 seed hash was a **placeholder and did not verify**. It was replaced with a real bcrypt hash and the database was reseeded. Application code does **not** hard-code the demo password.

### RBAC and scoping

| Check | Result |
|---|---|
| Unauthenticated access to business APIs | HTTP 401 |
| Field officer / approver `POST /api/projects` | HTTP 403 |
| ADMIN project list | 8 projects |
| Officer project list | 3 (Telangana only) |
| Field officer parcel list | 8 assigned parcels |

### Dashboard (values from PostgreSQL, not hard-coded)

Example national KPIs from the seeded DB:

| KPI | Value |
|---|---|
| Total projects | 8 |
| Area notified | 102.34 ha |
| Area acquired | 32.19 ha |
| Compensation assessed | ₹ 29,10,38,400 |
| Compensation paid | ₹ 21,59,70,300 |
| Affected families | 51 |
| Displaced families | 17 |
| Delayed projects | 1 |
| Projects at risk | 2 |

Notified area and acquired area are **separate metrics**. Filter `state=TG` reduces total projects from 8 → 3.

Charts returned: stage distribution, state-wise progress, compensation, R&R status, risk (from stored synthetic ML rows).

### Projects / parcels / acquisitions

- Project list, search, filters, pagination, detail, 404  
- Project create/patch for ADMIN and Acquisition Officer only  
- Parcel list, ULPIN search, filters, pagination, detail, GeoJSON `Feature`  
- Owner fields in parcel APIs: **name, ownership type, share only**  
- **Not** returned: `id_number`, `phone`, `address`, password hashes  
- Acquisition list (60 cases), detail, chronological timeline  
- **No** workflow transition endpoints (that is Phase 3)

---

## 3. Architecture (unchanged)

```
React (not built yet)
    │  REST JSON
    ▼
FastAPI
    ├── JWT auth
    └── RBAC + geo/assignment scope
            ▼
        Service layer
            ▼
        Repository layer
            ▼
    PostgreSQL 16/17 + PostGIS
```

Layers added:

- **Routers** — HTTP only  
- **Services** — login, KPI assembly, scoping  
- **Repositories** — SQLAlchemy queries (pagination, no N+1 on parcel owners)

Errors:

```json
{ "error": { "code": "UNAUTHORIZED", "message": "...", "details": {} } }
```

Success:

```json
{ "data": {}, "meta": { "data_source": "SYNTHETIC", "disclaimer": "..." } }
```

---

## 4. Files in this step

**New**

- `backend/app/main.py`, `errors.py`, `security.py`, `deps.py`, `logging.py`
- `backend/app/api/` — auth, dashboard, projects, parcels, acquisitions
- `backend/app/schemas/`
- `backend/app/repositories/`
- `backend/app/services/`
- `backend/tests/test_auth.py`, `backend/tests/test_api.py`

**Updated**

- `backend/app/config.py`, `backend/app/db.py`
- `backend/requirements.txt`, `.env.example`, `README.md`
- `scripts/seed_db.py` (bcrypt hash only)

**Not redesigned:** Alembic migration, SQLAlchemy models, table relationships.

---

## 5. Testing

| Kind | Result |
|---|---|
| Automated | **38 passed** (14 Phase 1 DB + 24 Phase 2 API/auth) |
| Manual (live Uvicorn `:8000`) | Health, login, me, KPIs, charts, filters, projects, parcels, acquisitions, timeline, 401, field scope, four roles, Swagger, ReDoc |
| Phase 1 regression | **Pass** |

Do not claim “everything works” beyond what was actually run above.

---

## 6. Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | No | Health check |
| GET | `/docs` | No | Swagger |
| GET | `/redoc` | No | ReDoc |
| POST | `/api/auth/login` | No | Login |
| GET | `/api/auth/me` | Yes | Current user |
| GET | `/api/dashboard/kpis` | Yes | KPIs from SQL |
| GET | `/api/dashboard/charts` | Yes | Chart series from SQL |
| GET | `/api/dashboard/filters` | Yes | Filter options |
| GET | `/api/projects` | Yes | Project list |
| GET | `/api/projects/{id}` | Yes | Project detail |
| POST | `/api/projects` | Yes (ADMIN, officer) | Create project |
| PATCH | `/api/projects/{id}` | Yes (ADMIN, officer) | Update project |
| GET | `/api/parcels` | Yes | Parcel search/list |
| GET | `/api/parcels/{id}` | Yes | Parcel detail + GeoJSON |
| GET | `/api/acquisitions` | Yes | Case list |
| GET | `/api/acquisitions/{id}` | Yes | Case detail |
| GET | `/api/acquisitions/{id}/timeline` | Yes | Append-only history |

---

## 7. How to run this step

```bash
docker compose up -d db          # or local Postgres: user/db/password nlamp
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
python ../scripts/seed_db.py     # or python ../scripts/demo_reset.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
python -m pytest -q
```

Copy `.env.example` → `.env`. Set `JWT_SECRET_KEY` if this is not a local demo.

---

## 8. Explicitly out of this step

- React / Vite UI  
- Proposal approve/reject  
- Acquisition stage transitions  
- Compensation / possession / R&R / field-submit writes  
- ML train/predict  
- Notifications, advanced reports  
- Live government APIs  

---

## 9. Known limitations

1. Dashboard **date-range** filters were deferred (state/district/project/stage/status work).  
2. Default `JWT_SECRET_KEY` is for **development only**.  
3. Docker was not used in the implementation environment; local PostgreSQL 17 + PostGIS was. `docker-compose.yml` still targets PostgreSQL **16** + PostGIS for other machines.

---

## 10. Next step (not started)

**Phase 3 — workflow:** proposal approval as the only approval action; then create/activate cases and append-only stage transitions. Still no frontend unless a later brief says otherwise.
