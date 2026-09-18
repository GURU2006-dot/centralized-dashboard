# SIH 26016 — Phase 4A Report

**Problem:** National Land Acquisition Management & Intelligence Platform (PS 26016)  
**Step:** React frontend / government command center  
**Date:** 2026-09-08  
**Status:** **COMPLETE** (implementation). In-browser visual click-through of every screen was **not** run; API, proxy, production build, and backend regression **were**.

Do not start Phase 4B from this report.

All UI figures are **synthetic demonstration data**. They are not live land records, cadastral maps, or government statistics.

No database schema change. No ML training. No live government integrations. Alembic head remains `7f0736d5b557`.

---

## 1. Phase 4A status

Implemented a Vite + React SPA under `/home/user/frontend` that consumes the existing FastAPI envelope (`{ data, meta }`) and JWT login.

The synthetic-data banner is always visible.

---

## 2. What was implemented

P0: login, JWT session, RBAC-aware shell, dashboard KPIs/charts from `/api/dashboard/*`, projects, parcels, GIS (Leaflet + real parcel GeoJSON), proposals (create/edit/submit/verify/approve/reject), acquisition cases, workflow timeline + sequential transition.

P1: compensation, possession, families, rehabilitation, resettlement, field verification (GPS via browser geolocation, checks, photo upload, submit), documents (local-disk disclaimer), alerts, notifications, audit, analytics (dashboard APIs).

P2: reports viewing (export labelled unavailable), integrations MOCK cards, users placeholder (no user API), settings/logout.

---

## 3. Frontend architecture

```
Browser
  └── Vite :5173  (proxy /api and /health → FastAPI :8000)
        └── React Router
              ├── AuthContext (JWT in sessionStorage)
              ├── api/* Axios client (Authorization header)
              └── pages + shared UI
```

Axios `baseURL` is empty so requests stay same-origin. The user browser never calls `127.0.0.1:8000`.

Stack: React 19, Vite 8, Tailwind CSS 4, React Router, Axios, Recharts, Leaflet / React Leaflet, Lucide.

No Redux.

---

## 4. Routes / pages

| Path | Page |
|---|---|
| `/login` | Login |
| `/` | Dashboard |
| `/projects`, `/projects/:id` | Projects |
| `/parcels`, `/parcels/:id` | Parcels |
| `/map` | GIS |
| `/proposals`, `/proposals/new`, `/proposals/:id` | Proposals |
| `/acquisitions`, `/acquisitions/:id` | Cases + timeline |
| `/workflow` | Stage tracker |
| `/compensation`, `/possession`, `/families`, `/rehabilitation`, `/resettlement` | C&R |
| `/field`, `/field/:id` | Field verification |
| `/documents` | Documents |
| `/analytics`, `/reports`, `/alerts` | Intelligence |
| `/notifications`, `/integrations`, `/audit`, `/users`, `/settings` | System |

Unauthorized roles hitting a URL see an in-app forbidden state. Backend 403 remains authoritative.

---

## 5. API integrations

Central client: `frontend/src/api/client.js`. Modules wrap:

`/api/auth/login`, `/me`  
`/api/dashboard/kpis|charts|filters`  
`/api/projects`, `/api/parcels`  
`/api/proposals` + submit/verify/approve/reject  
`/api/acquisitions` + timeline + transition  
`/api/compensation`, `/possession`, `/families`, `/rehabilitation`, `/resettlement`  
`/api/field-verification` + photos + submit  
`/api/documents`  
`/api/alerts`, `/notifications`, `/audit`

GIS has **no dedicated GeoJSON collection endpoint**. The map lists parcels then loads each parcel detail’s `geometry` Feature. Coordinates are not invented.

---

## 6. RBAC

Roles from `/api/auth/me`: `ADMIN`, `ACQUISITION_OFFICER`, `APPROVING_AUTHORITY`, `FIELD_OFFICER`.

Sidebar items filtered by role. Mutation buttons hidden when the role cannot call the API. Field officer `/api/proposals` returns 403 (verified via proxy).

JWT stored in `sessionStorage` (not logged). 401 clears session and redirects to `/login`.

---

## 7. GIS

`ParcelMap` uses React Leaflet + OSM tiles + GeoJSON polygons styled by `acquisition_status`. Popup shows ULPIN, khasra, village, district, state, area, status. Click navigates to parcel detail. Fit-to-bounds on loaded features.

---

## 8. Responsive / mobile

Sidebar is a drawer below `lg`. Field verification is a single-column, large tap-target form with `capture="environment"` on photo input and a Capture GPS button (`navigator.geolocation`; failure does not invent coordinates). Tables scroll horizontally. KPI grid collapses from 5 → 2 columns.

Visual device QA was **not** executed.

---

## 9. Testing performed

| Check | Result |
|---|---|
| `npm run build` | Success |
| Vite `npm run dev` on `0.0.0.0:5173` | Running |
| `GET /` SPA | 200 |
| Vite proxy `GET /health` | 200 `{"status":"ok"}` |
| Proxy login `admin@demo.local` | 200 token |
| Proxy KPIs | `total_projects = 8` |
| Proxy projects / parcels / cases | 200 |
| Parcel GeoJSON | `Feature` with geometry |
| Field officer field list | 200, 8 rows |
| Field officer proposals | 403 |
| Bad login | 401 |
| Headed browser walkthrough | **NOT TESTED** |

---

## 10. Backend regression

```
python3 scripts/demo_reset.py
cd backend && python3 -m pytest -q
→ 45 passed
```

A run **without** reset failed `total == 60` because earlier Phase 3 tests had created extra cases. That is pre-existing seed mutation, not a frontend defect. After `demo_reset`, all 45 tests pass.

---

## 11. Backend changes

**None.** CORS still defaults to `http://localhost:5173`. Preview traffic uses the Vite proxy, so extra CORS origins were not required.

---

## 12. Known limitations

1. GIS loads geometries by N parcel-detail requests (no bulk GeoJSON API). Capped at 40 parcels per filter page.  
2. No authenticated binary download for documents.  
3. Compensation / possession / R&R workbenches are case-picker UIs because those APIs are per-case, not global lists.  
4. Bundle ~920 kB gzip ~272 kB (Leaflet + Recharts in the main chunk).  
5. Default JWT secret remains development-only.

---

## 13. Placeholder screens

| Screen | Label |
|---|---|
| Users & Roles | COMING IN PHASE 4B — no users API |
| Integrations | MOCK / DEMONSTRATION — no live government APIs |
| Reports export | Unavailable — no PDF API; no fake PDF |
| ML predict | Not in Phase 3 API; analytics uses stored synthetic risk charts only |

---

## 14. Commands

```bash
# Postgres 17 + PostGIS already local: nlamp/nlamp @ localhost:5432/nlamp
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
python ../scripts/demo_reset.py
uvicorn app.main:app --host 0.0.0.0 --port 8000

cd ../frontend
npm install
npm run dev
# http://localhost:5173
```

Demo emails: `admin@demo.local`, `officer@demo.local`, `approver@demo.local`, `field@demo.local`. Password is the existing demo password; it is **not** hard-coded in the frontend.

---

## 15. Recommended Phase 4B

Only if a later brief requires it: ML train/predict UI against a real backend endpoint, bulk GeoJSON, document download, user admin APIs, or export. Do **not** connect live government systems unless that brief says so.

---

Phase 4A **STOP**.
