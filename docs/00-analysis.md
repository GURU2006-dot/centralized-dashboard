# Spec analysis — SIH 26016

## 1. Problem in one sentence

A single web platform that lets land-acquisition officers run the RFCTLARR-style lifecycle (proposal → possession → R&R), lets authorities approve, lets field staff geo-verify on a phone, and lets administrators see a **national KPI dashboard** — with GIS, alerts, and a **delay-risk** Random Forest — as a **one-day SIH prototype** on synthetic data.

## 2. Requirement → module map

| Spec req | Capability | Module(s) | MVP priority |
|---|---|---|---|
| R7 | End-to-end digital workflow | `acquisition_cases` + `workflow_events` + `/api/acquisitions` + Acquisition Workflow page | **P0** |
| R8 | Proposal submit / verify / approve / track | `proposals` + `/api/proposals` + Proposal pages | **P1** (track on P0 via cases) |
| R9 | Geo-tag, spatial viz, parcel viz | Leaflet + `/api/gis` + PostGIS/GeoJSON | **P0** |
| R10 | National dashboard KPIs | `/api/dashboard` + Dashboard page + seed aggregations | **P0** |
| R11 | API integration architecture | `app/integrations/*` adapters + mock implementations | **P2 live / P0 mock adapter** |
| R12 | Mobile-responsive field UI | Responsive React; Field Verification page | **P1** (layout P0) |
| Add-on | RBAC | JWT + role dependency | **P0** |
| Add-on | Alerts / notifications | rules engine (in-process) + `/api/alerts` | **P1** |
| Add-on | Customizable dashboards | saved filter presets (admin) | **P2** |
| Add-on | Analytical reports | `/api/reports` + Reports page | **P1** |
| Add-on | Predictive analytics | `app/ml` + `POST /api/ml/predict-delay` | **P0** |
| Add-on | Audit logging | `audit_logs` + middleware | **P0** (write path); admin viewer **P1** |
| Add-on | Secure API | JWT, RBAC, validated Pydantic, no secrets in frontend | **P0** |

Citizen / affected-person portal: **explicitly out of one-day MVP**. Schema does **not** require a `CITIZEN` role for P0.

## 3. What “one-day prototype” actually means

A judging demo must show, with seeded data and four demo logins:

1. Login as each role and see different menus.
2. National dashboard KPI cards + 3–4 charts + filters.
3. Search a parcel by ULPIN / khasra and open details.
4. Advance an acquisition case through stages (timeline + audit).
5. Leaflet map: project → click parcel → popup with status.
6. Call Random Forest, show LOW/MEDIUM/HIGH + score, with a **synthetic-model** banner.
7. Data survives refresh (PostgreSQL).

P1 (proposals, approve/reject, alerts, compensation, field verify, basic reports) should be in the same binary if time remains; they are designed so they can be stubbed with seed data even if write-APIs are thin.

## 4. Explicit non-goals (do not build)

- Live BhuNaksha / DILRMP / NGDRS / PFMS connections.
- Native Android/iOS app.
- Microservices, message bus, Kafka, Redis (unless we later need a cache; not day-one).
- Blockchain land registry.
- LLM / extra ML models beyond Random Forest delay risk.
- Production-grade object storage, SSO, Aadhaar eKYC.
- Claiming the RF model is trained on real government history.

## 5. External API reality (R11)

| System | Publicly usable in SIH lab? | Prototype stance |
|---|---|---|
| DILRMP / ULPIN land records | **No** — state/DoLR authorization | `LandRecordsAdapter` **mock** |
| BhuNaksha / cadastral WMS/WFS | **No** — licensed / state GIS | `CadastralMapAdapter` **mock** + synthetic GeoJSON |
| SRO / registration (NGDRS) | **No** | `RegistrationAdapter` **mock** |
| State acquisition MIS | **No** | `AcquisitionDataAdapter` **mock** |
| OpenStreetMap raster tiles | **Yes** — public tile servers | Used by Leaflet for **basemap only**, not cadastral truth |
| Nominatim geocoding | Optional, public, rate-limited | Not required for MVP |

Every API response and parcel row carries `data_source`: `SYNTHETIC` | `MOCK_ADAPTER` | `EXTERNAL`.  
`EXTERNAL` is never set in the prototype seed.

## 6. Domain model (RFCTLARR-aligned, simplified)

```
Proposal (DRAFT→…→APPROVED/REJECTED)
    └── selects Project + N Land Parcels
            └── each parcel has 1 AcquisitionCase in a Project
                    └── WorkflowEvent* (append-only)
                    └── Compensation 0..1
                    └── Possession 0..1
                    └── FieldVerification*
                    └── Documents*
            └── AffectedFamily* (project-level, optionally parcel-linked)
                    └── Rehabilitation 0..1
                    └── Resettlement 0..1
```

Workflow stage catalogue (ordered, extendable without migrations of business logic):

1. `PROPOSAL`  
2. `SUBMISSION`  
3. `VERIFICATION`  
4. `SIA`  
5. `APPROVAL`  
6. `NOTIFICATION`  
7. `AWARD`  
8. `COMPENSATION_ASSESSMENT`  
9. `COMPENSATION_PAID`  
10. `POSSESSION`  
11. `REHABILITATION_RESETTLEMENT`  
12. `COMPLETED`

New stages = new catalogue rows + next-stage rules in config, not a rewrite.

## 7. Assumptions

| ID | Assumption |
|---|---|
| A1 | Single PostgreSQL 16 database; PostGIS enabled via official PostGIS image. |
| A2 | Document binaries stored on local disk (`/data/uploads`) in the prototype; metadata in PostgreSQL. |
| A3 | Auth is username/email + password, JWT access token (8h, fine for a demo day). No refresh-token rotation. |
| A4 | One user has exactly one role (no multi-role accounts) to keep RBAC trivial. |
| A5 | Geographic scope of seed data: 3 states, ~6 districts, ~8 projects, ~80 parcels — enough for filters and a map, small enough to seed in seconds. |
| A6 | Area unit: **hectares**. Currency: **INR**. |
| A7 | ULPIN stored as `VARCHAR(14)` (DoLR 14-character unique parcel ID) but values are synthetic. |
| A8 | Leaflet consumes GeoJSON from our API; OSM tiles are background only. |
| A9 | Alert evaluation runs synchronously on workflow transitions and via `POST /api/alerts/evaluate` (demo button). No Celery. |
| A10 | ML model is trained offline (`train.py`) on synthetic CSV; `model.pkl` is committed or generated in setup. Inference in-process. |
| A11 | Hindi/English i18n is **not** in MVP; UI is English with Indian administrative terms (khasra, tehsil, ULPIN). |
| A12 | Approving Authority can approve proposals; stage transitions on cases are performed by Acquisition Officer except `APPROVAL` / `REJECTED` which require Approving Authority. |

## 8. Unresolved questions (do not block architecture)

| ID | Question | Default if unanswered |
|---|---|---|
| Q1 | Exact SIH evaluation environment (Docker allowed?) | Ship `docker-compose.yml` + README local-venv path. |
| Q2 | Whether judges have PostgreSQL preinstalled | Compose file is the default. |
| Q3 | Real state shapefiles for choropleth | Use approximate state centroids + bar charts; optional simplified GeoJSON in `/data/geo`. |
| Q4 | Compensation formula (RFCTLARR multiplier) | Manual assessed/paid amounts; no statutory calculator in MVP. |
| Q5 | Multi-parcel proposals vs one case per parcel | Both: proposal M:N parcels; **one `acquisition_cases` row per (project, parcel)**. |

## 9. Risk register (prototype)

| Risk | Mitigation |
|---|---|
| PostGIS install friction on Windows laptops | Fallback: `geometry_geojson JSONB`; same API contract. |
| Leaflet + many polygons lag | Seed ≤100 parcels; simplify geometries. |
| RF model pickle/sklearn version skew | Pin `scikit-learn` in `requirements.txt`; train during setup. |
| Demo login confusion | Four well-known demo users on the login page footer. |
| Scope creep into P2 | Execution plan timeboxes P0 first; P2 is slides + `/api/integrations/status` page. |
