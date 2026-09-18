# J. Architecture decisions

Each decision is tied to a spec constraint. No extra technology without a reason.

---

### ADR-001 — Modular monolith, not microservices

**Decision:** One FastAPI process, one React SPA, one PostgreSQL.  
**Why:** Spec rule 6: avoid unnecessary microservices. A one-day SIH team cannot operate a service mesh. Modules (`api`, `services`, `ml`, `integrations`) give later split potential without day-one ops cost.  
**Rejected:** Separate ML service, GIS service, notification service.

### ADR-002 — PostgreSQL + PostGIS (JSONB fallback)

**Decision:** Postgres 16 with PostGIS geometry on `land_parcels`. If the laptop cannot load PostGIS, store `geometry_geojson JSONB` and keep the same GeoJSON API.  
**Why:** Spec names PostgreSQL; GIS is P0; PostGIS is the native type for parcels. Official `postgis/postgis` image is one compose line — practical for the prototype.  
**Rejected:** MongoDB, SQLite+spatialite (spec says PostgreSQL), Elasticsearch.

### ADR-003 — Leaflet, not MapLibre/Google Maps

**Decision:** Leaflet as specified. OSM raster tiles for basemap.  
**Why:** Spec §4 / §9. OSM is the only **AVAILABLE_VERIFIED** map source. Google Maps needs keys; MapLibre is extra.  
**Caveat:** OSM is **not** cadastral data. UI disclaimer required.

### ADR-004 — In-process Random Forest, not a model server

**Decision:** `scikit-learn` RF, `model.pkl` loaded in the API process, isolated package `app/ml`.  
**Why:** Spec §13–14. One prediction per button click; latency is milliseconds. No GPU, no extra AI.  
**Rejected:** XGBoost (not requested), neural nets, hosted inference.

### ADR-005 — Synthetic data with an explicit `data_source` column

**Decision:** Every parcel/project/prediction stamped `SYNTHETIC` | `MOCK_ADAPTER` | `EXTERNAL`. Seed never uses `EXTERNAL`.  
**Why:** Spec rules 2–4, §21. Judges and later auditors can see the difference.  
**Rejected:** Silent fake “Live DILRMP” labels.

### ADR-006 — Mock adapters behind a Protocol, not fake HTTP to invented URLs

**Decision:** `LandRecordsPort` et al. + mock implementations + `NotImplemented` external stubs that 503.  
**Why:** Spec §11, §15, “do not invent government APIs”. Architecture is demonstrable via `/api/integrations/status`.  
**Rejected:** Hard-coding `https://dolr.gov.in/api/...` or scraping.

### ADR-007 — JWT access tokens, one role per user

**Decision:** HS256 JWT, 8h, bcrypt passwords, `require_roles` dependency.  
**Why:** Fast to implement, works with Vite SPA, matches “secure API” without Keycloak. One role keeps the matrix understandable for a demo.  
**Rejected:** Session cookies (CSRF + CORS complexity), OAuth (no IdP), ABAC.

### ADR-008 — Append-only workflow events + stage catalogue

**Decision:** Stages are rows in `workflow_stage_definitions`; transitions append `workflow_events`; engine checks an allow-list.  
**Why:** Spec §6: extend without rewrite; every transition needs status, time, user, remarks, documents, audit.  
**Rejected:** JSON blob of status on the project only; a hardcoded 12-way `if/else` scattered in routers.

### ADR-009 — One acquisition case per (project, parcel)

**Decision:** Unique `(project_id, parcel_id)` on `acquisition_cases`. Proposals are M:N to parcels and spawn cases on approve.  
**Why:** Compensation, possession, and ML hang naturally off a case. Matches land-acquisition practice (parcel is the unit of award).  
**Rejected:** One case per project (too coarse for parcel GIS) or only proposal-level tracking (loses R7 per-parcel lifecycle).

### ADR-010 — Local disk for documents

**Decision:** Files under `data/uploads/{uuid}` plus `documents` metadata. 10 MB cap.  
**Why:** One-day prototype; S3/MinIO is ops. Spec does not require a DAM.  
**Rejected:** Storing blobs in PostgreSQL BYTEA (backup pain).

### ADR-011 — In-process alert rules, no broker

**Decision:** `alert_service.evaluate_*` on workflow transition and admin POST. Insert `alerts` rows.  
**Why:** Spec lists five simple IF rules. Celery/Redis is P2 “enterprise notification infrastructure”.  
**Rejected:** Email/SMS gateways, Firebase.

### ADR-012 — REST/JSON only

**Decision:** FastAPI routers as in §17; no GraphQL, no gRPC.  
**Why:** Spec §4. Pydantic schemas = the contract in [C-api-contracts.md](./C-api-contracts.md).  
**Rejected:** tRPC, OpenAPI-first codegen (nice, not needed today).

### ADR-013 — Layered FastAPI (api → schemas → services → repositories)

**Decision:** Follow spec §17 literally.  
**Why:** Keeps ML and integrations off routers; testable services. For speed, a repository can be a thin session query — not a generic ORM framework.  
**Rejected:** Fat controllers; Django.

### ADR-014 — React/Vite/Tailwind/Recharts as specified

**Decision:** No Next.js, no MUI, no D3.  
**Why:** Spec §4. Vite is the fastest SPA boot for a hackathon. Recharts covers all listed dashboard charts. Shared components listed in D.  
**Rejected:** Native mobile (spec §19). Responsive SPA meets R12.

### ADR-015 — Area in hectares, money in INR, ULPIN as VARCHAR(14)

**Decision:** Documented in assumptions A6–A7.  
**Why:** Indian land-acquisition reporting. No multi-currency.

### ADR-016 — No blockchain, no extra AI, no citizen portal in MVP

**Decision:** Follow spec rules 7–8 and §22 P2.  
**Why:** None of these are needed to demonstrate R7–R12. Citizen support is optional and explicitly not required for the one-day MVP.

### ADR-017 — Tests: a handful, not coverage theatre

**Decision:** `test_auth`, `test_dashboard`, `test_parcels`, `test_workflow`, `test_ml_predict` if time.  
**Why:** Protect demo-breakers. Full suite is not the SIH scoring rubric.

### ADR-018 — English UI with Indian domain terms

**Decision:** No i18n framework.  
**Why:** One day. Labels use khasra, tehsil, ULPIN, R&R.

---

## Mapping back to requirements

| Decision | Requirements served |
|---|---|
| ADR-001, 013, 012 | Maintainability, §17 |
| ADR-002, 003 | R9 GIS |
| ADR-004 | §13–14 predictive analytics P0 |
| ADR-005, 006 | R11 + honesty rules |
| ADR-007 | RBAC, secure API, P0 auth |
| ADR-008, 009 | R7 workflow, R8 proposals |
| ADR-010 | Documents, R12 photos |
| ADR-011 | Alerts |
| ADR-014 | R10 dashboard, R12 mobile |
| ADR-016 | Scope control for one-day MVP |

---

## Explicitly not decided / not needed

- Multi-region deployment
- Observability stack (Prometheus, etc.)
- Fine-grained permission tables
- Statutory compensation calculator (RFCTLARR First Schedule)
- Digital signature of awards
