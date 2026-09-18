# H. Implementation plan

Sequential tasks for **after** this architecture pack is accepted.  
Do not start these until the team is ready to write code.

Each task: objective, files, dependencies, output, acceptance.

---

### T0 — Repository skeleton

- **Objective:** Empty tree, tooling, env, compose, README disclaimer.
- **Files:** root `README.md`, `docker-compose.yml`, `.env.example`, `backend/requirements.txt`, `frontend/package.json`, Vite/Tailwind configs, `data/README.md`.
- **Deps:** none.
- **Output:** `docker compose up -d db` yields healthy PostGIS; `npm install` / `pip install` succeed.
- **Accept:** Postgres accepts connections; no app code required beyond FastAPI hello optional.

### T1 — Database models + Alembic initial migration

- **Objective:** All entities in [B-database-erd.md](./B-database-erd.md).
- **Files:** `backend/app/models/*`, `alembic/versions/0001_initial.py`, enums.
- **Deps:** T0.
- **Output:** `alembic upgrade head` creates tables, FKs, indexes, PostGIS columns (or JSONB fallback).
- **Accept:** `\dt` lists all tables; inserting a parcel with geom works.

### T2 — Seed synthetic data

- **Objective:** Realistic demo graph + GeoJSON + ML CSV.
- **Files:** `data/seed/*.csv`, `data/geo/parcels.geojson`, `data/ml/train.csv`, `scripts/seed_db.py`.
- **Deps:** T1.
- **Output:** 3 states, ≥6 districts, ≥8 projects, ≥80 parcels with polygons, owners, cases across all 12 stages, compensation mix, families, alerts, documents metadata, 4 users.
- **Accept:** Every dashboard KPI is non-zero; GIS returns features; `data_source=SYNTHETIC` on operational rows.

### T3 — Auth + RBAC

- **Objective:** Login, JWT, role deps, `/me`.
- **Files:** `security.py`, `deps.py`, `api/auth.py`, `api/users.py`, `services/auth_service.py`, schemas.
- **Deps:** T1–T2.
- **Output:** Four demo logins; admin can list users.
- **Accept:** Wrong password 401; field token 403 on `POST /api/users`; `/api/auth/me` returns role.

### T4 — Audit helper

- **Objective:** `audit_service.record` used by later services.
- **Files:** `models/audit.py`, `services/audit_service.py`, `api/audit.py`.
- **Deps:** T3.
- **Output:** Admin can page logs (may be empty until T5+).
- **Accept:** Manual insert visible on `GET /api/audit-logs`.

### T5 — Projects + parcels APIs

- **Objective:** CRUD/search for P0 parcel search and details.
- **Files:** `api/projects.py`, `api/parcels.py`, repos, services, schemas.
- **Deps:** T3.
- **Output:** Search by ULPIN, khasra, owner, state, district; parcel detail payload complete.
- **Accept:** Seed ULPIN round-trips; 409 on duplicate ULPIN; geo scope hides other-state parcels for scoped officer.

### T6 — Workflow engine + acquisition APIs

- **Objective:** Catalogue + legal transitions + timeline + audit.
- **Files:** `workflow/stages.py`, `workflow/engine.py`, `api/acquisitions.py`, `services/workflow_service.py`.
- **Deps:** T5.
- **Output:** `POST .../transition` moves stage, writes `workflow_events`.
- **Accept:** Illegal skip returns 400; event has user, timestamp, remarks; case `current_stage` updates.

### T7 — Dashboard + reports read APIs

- **Objective:** KPI cards and chart payloads.
- **Files:** `api/dashboard.py`, `services/dashboard_service.py`, `repositories/dashboard_repo.py`, `api/reports.py`.
- **Deps:** T5–T6.
- **Output:** Filtered KPIs matching §10 / §7.
- **Accept:** Filter `state_code=TG` changes totals; delayed_projects ≥ 0 and consistent with seed.

### T8 — GIS API

- **Objective:** GeoJSON FeatureCollections.
- **Files:** `api/gis.py`, `services/gis_service.py`.
- **Deps:** T5.
- **Output:** Project and bbox queries; disclaimer in `meta`.
- **Accept:** Valid GeoJSON; unfiltered over-cap 400; `data_source=SYNTHETIC`.

### T9 — ML train + predict

- **Objective:** RF artifact + `POST /api/ml/predict-delay`.
- **Files:** `app/ml/*`, `scripts/train_ml.py`, `api/ml.py`, `services/ml_service.py`.
- **Deps:** T6 (features from cases).
- **Output:** `model.pkl`; prediction persists; HIGH creates alert if T12 exists (else skip).
- **Accept:** Response shape `{risk_level, risk_score}`; disclaimer present; 503 if pickle missing.

### T10 — Frontend shell

- **Objective:** Vite app, Tailwind, router, layout, login, role sidebar, disclaimer.
- **Files:** `frontend/src/main.jsx`, `App.jsx`, `layouts/*`, `auth/*`, `pages/LoginPage.jsx`, `api/client.js`.
- **Deps:** T3 (backend running).
- **Output:** Login → dashboard route (page can be placeholder).
- **Accept:** Mobile drawer works; field user does not see Admin.

### T11 — Dashboard + parcel + GIS pages (P0 UI)

- **Objective:** Demonstrable national dashboard, search, detail, map.
- **Files:** `pages/DashboardPage.jsx`, `ParcelsPage.jsx`, `ParcelDetailPage.jsx`, `GisMapPage.jsx`, `components/dashboard/*`, `components/map/*`, `components/ui/*`.
- **Deps:** T7, T8, T10.
- **Output:** Filters, 10 KPI cards, charts, Leaflet click-through.
- **Accept:** Phone-width usable; OSM tiles + synthetic polygons; banner visible.

### T12 — Workflow UI + ML insights (P0 remaining)

- **Objective:** Stage timeline actions + predict button.
- **Files:** `AcquisitionWorkflowPage.jsx`, `MlInsightsPage.jsx`, `components/workflow/*`.
- **Deps:** T6, T9, T10.
- **Output:** Officer advances a case; ML page shows HIGH/MEDIUM/LOW.
- **Accept:** Timeline updates without reload; synthetic-model copy visible.

### T13 — Proposals (P1)

- **Objective:** DRAFT → SUBMITTED → UNDER_VERIFICATION → APPROVED/REJECTED.
- **Files:** backend proposal API/service; `ProposalsPage.jsx`, `ProposalFormPage.jsx`, `ProposalReviewPage.jsx`.
- **Deps:** T5, T6, T10.
- **Output:** Approver can reject with remarks; approve opens cases.
- **Accept:** Officer cannot approve (403); audit rows written.

### T14 — Documents + compensation + possession + R&R (P1)

- **Objective:** Upload/verify docs; track money, possession, families.
- **Files:** respective APIs, pages `CompensationPage.jsx`, `RRPage.jsx`, `FileUpload.jsx`.
- **Deps:** T5, T10.
- **Output:** Patch paid amount; R&R status edits.
- **Accept:** File download works; compensation KPI moves after patch + refresh.

### T15 — Field verification (P1)

- **Objective:** Mobile submit with GPS + photo.
- **Files:** field API, `FieldVerificationPage.jsx`, `FieldVerificationSubmitPage.jsx`.
- **Deps:** T5, T14 (photos as documents), T10.
- **Output:** Assigned list; submit requires GPS.
- **Accept:** Unassigned field officer 403; photo appears on parcel documents.

### T16 — Alerts + notifications (P1)

- **Objective:** Five rules on evaluate + on transition.
- **Files:** `services/alert_service.py`, `api/alerts.py`, `api/notifications.py`, `AlertsPage.jsx`, `AlertBell`.
- **Deps:** T6, T9, T14, T15.
- **Output:** Admin “Evaluate rules”; unread badge.
- **Accept:** Overdue seeded case yields `STAGE_OVERRUN` or `APPROVAL_PENDING`; HIGH ML → `ML_HIGH_RISK`.

### T17 — Integrations status + mock lookup (P2 surface, small)

- **Objective:** Honest adapter page and mock lookup.
- **Files:** `app/integrations/*`, `api/integrations.py`, Admin tab.
- **Deps:** T5, T10.
- **Output:** Status JSON; lookup seeded ULPIN via mock.
- **Accept:** Copy says APIs unavailable; `data_source=MOCK_ADAPTER`; no fake live URLs.

### T18 — Reports page + polish + demo reset

- **Objective:** Basic reports; `scripts/demo_reset.py`; README demo script (5 minutes).
- **Files:** `ReportsPage.jsx`, `AdminPage.jsx` audit tab, README, `demo_reset.py`.
- **Deps:** T7, T11–T16.
- **Output:** Judge path documented.
- **Accept:** Fresh compose + seed + train + two processes; all P0 clicks work.

---

## Dependency graph (summary)

```
T0 → T1 → T2 → T3 → T4
              T3 → T5 → T6 → T7
                    T5 → T8
                    T6 → T9
T3 → T10 → T11 (needs T7,T8)
         → T12 (needs T6,T9)
         → T13 → T14 → T15 → T16
T5 → T17
T7 → T18
```

P0 slice = T0–T12.  
P1 slice = T13–T16.  
P2/demo = T17–T18.
