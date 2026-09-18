# SIH 26016 — Final architecture (as implemented)

**Stack:** modular monolith — FastAPI + React (Vite) + PostgreSQL 16/17 PostGIS.  
**Alembic head:** `7f0736d5b557` (single initial migration).  
**Honesty:** operational rows `data_source=SYNTHETIC`. ML `trained_on=SYNTHETIC`. Integrations `INTEGRATION_MODE=mock`. No live government APIs, credentials, or invented endpoints.

Architecture freeze corrections remain in force ([architecture-freeze.md](./architecture-freeze.md), [J-architecture-decisions.md](./J-architecture-decisions.md)).

---

## 1. Runtime diagram

```
Browser (React SPA :5173)
   │  relative /api  (Vite proxy in dev)
   ▼
FastAPI (uvicorn :8000)
   │  api → schemas → services → repositories
   ├─ JWT RBAC (ADMIN | ACQUISITION_OFFICER | APPROVING_AUTHORITY | FIELD_OFFICER)
   ├─ workflow engine (proposal status ≠ case stages)
   ├─ app.ml.predictor  (sklearn RF, no FastAPI/SQLAlchemy imports)
   └─ integrations ports → Mock* adapters (external mode 503, fail closed)
         │
         ▼
PostgreSQL + PostGIS
  land_parcels.geom, ml_predictions, workflow_events (append-only), audit_logs
```

No Kafka, Redis, extra microservices, LLM, or model server.

---

## 2. Frontend

- Vite + React + Tailwind + Recharts + Leaflet.
- `baseURL: ""` so the SPA never hard-codes API hosts; production must reverse-proxy `/api` and `/health`.
- Role-filtered nav (`frontend/src/lib/roles.js`). Backend is the security boundary.
- Pages: dashboard, projects, parcels, GIS, proposals, acquisitions + workflow, compensation, families, R&R, possession, field (phone-first), documents, analytics, model card, reports (view-only), alerts, notifications, integrations, audit, users (no user-admin API), settings.
- Synthetic banner on login and app shell.

---

## 3. Backend modules

| Layer | Path |
|---|---|
| HTTP | `backend/app/api/*.py` mounted at `/api` |
| Schemas | `backend/app/schemas/` |
| Services | `backend/app/services/` (workflow, proposals, ML persist, alerts, GIS) |
| Repositories | `backend/app/repositories/` |
| ML (pure) | `backend/app/ml/` — dataset, features, train, predictor |
| Adapters | `backend/app/integrations/` |

Health: `GET /health` → `{ "status": "ok" }`.

---

## 4. Auth / RBAC

- HS256 JWT, bcrypt, 8h default (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).
- One role per user. Geographic scope: officer `state_code=TG`; field officer assigned parcels only.
- Owner `id_number`, `phone`, `address` are **not** in general parcel JSON.

| Action | ADMIN | Officer | Approver | Field |
|---|---|---|---|---|
| Dashboard / parcels / GIS / cases (scoped) | ✓ | ✓ | ✓ | ✓ (assigned) |
| Create project / proposal / transition | ✓ | ✓ | ✗ | ✗ |
| Approve / reject proposal | ✓ | ✗ | ✓ | ✗ |
| ML predict | ✓ | ✓ | ✓ | ✗ |
| Field submit / photos | ✓ | ✗ | ✗ | ✓ |
| Integrations sync / audit | ✓ | ✗ | ✗ | ✗ |

---

## 5. Proposal vs case workflow

**Proposal statuses:** `DRAFT → SUBMITTED → UNDER_VERIFICATION → APPROVED | REJECTED`.  
**This is the only approval action.**

**Case stages (catalogue):**  
`SIA → NOTIFICATION → AWARD → COMPENSATION_ASSESSMENT → COMPENSATION_PAID → POSSESSION → REHABILITATION_RESETTLEMENT → COMPLETED`

- Cases are created **only** when a proposal is APPROVED (one case per proposal parcel / unique project+parcel).
- Engine rejects skipped stages (400).
- COMPENSATION_PAID requires paid compensation; COMPLETED requires possession `TAKEN`.
- `workflow_events` are append-only.

---

## 6. Database (implemented)

PostgreSQL + PostGIS. Core entities: `roles`, `users`, `states`, `districts`, `projects`, `land_parcels` (geom), `owners` / `parcel_owners`, `proposals` / `proposal_parcels`, `workflow_stage_definitions`, `acquisition_cases`, `workflow_events`, `documents`, `compensation`, `affected_families`, `rehabilitation`, `resettlement`, `possession`, `field_verifications`, `notifications`, `alerts`, `ml_predictions` (`risk_score` 0–1 CHECK), `audit_logs`.

Full column catalogue: [B-database-erd.md](./B-database-erd.md).

---

## 7. ML

- Offline train: `python -m app.ml.train` / `scripts/train_ml.py`. Artifact `backend/app/ml/artifacts/delay_risk_model.joblib`.
- Features only from real schema (19 names in `app/ml/features.py`). No owner PII. No invented `APPROVAL` case stage.
- Display score = expected class midpoint `0·P(LOW)+50·P(MEDIUM)+100·P(HIGH)`, clamped 0–100. Stored `risk_score` = display/100 (still 0–1). **Not** a calibrated P(delay). **Not** raw P(HIGH)×100 (that collapsed almost every live score into LOW).
- Categories: LOW ≤39, MEDIUM ≤69, HIGH ≥70 — prototype conventions.
- HIGH → `AlertService` rule `ML_HIGH_RISK`, unread-alert dedup.

Train metrics (do not inflate): accuracy **0.7792**, f1_macro **0.6088**, roc_auc_ovr **0.866**.

---

## 8. GIS

`GET /api/gis/parcels` → GeoJSON FeatureCollection (limit 80) with ULPIN, status, stage, risk. Leaflet colours by risk/status/stage. Coordinates are stored PostGIS polygons, never invented.

---

## 9. Integrations

Ports + mock implementations only. `GET /api/integrations/status` → `mode: mock`. Lookup returns MOCK DTOs for seeded ULPINs. Sync: `synced: 0`. External mode stubs **503**.

---

## 10. Documents / field GPS

- Uploads to local disk (`data/uploads`), metadata in `documents`.
- Field GPS comes from the browser Geolocation API. Failure → error toast; **no fabricated lat/lng**. Submit without GPS → 400.

---

## 11. Deployment

- Dev: uvicorn `:8000` + Vite `:5173` with proxy.
- Production frontend: `npm run build` → `frontend/dist`; serve behind a reverse proxy to the API.
- `docker-compose.yml` starts **PostGIS only**. Full app images are not in this prototype. This evaluation environment had **no Docker CLI**.
- Config: copy `.env.example` → `.env`. Replace `JWT_SECRET_KEY` outside demo.

---

## 12. What this prototype is not

- Not live DILRMP / DoLR / state cadastral / registration / PFMS.
- Not a statutory compensation calculator or digital-signature award system.
- Not a citizen portal, Kafka bus, or LLM assistant.
- Frontend is not the security boundary.
