# I. One-day execution plan

Assume **~10 working hours** after architecture (this document) is done.  
Optimize for a **live judging demo**, not completeness.

Team shape that fits the plan (adjust if solo — then drop P1 write-paths and keep P1 as **read-only seed screens**):

| Track | Owner |
|---|---|
| A — Backend / DB / ML | 1–2 people |
| B — Frontend | 1–2 people |
| C — Data + demo narrative | 1 person (can overlap A) |

If **one person:** follow the same clock but skip T14 write UI (use seed data displays) and T17 until the last 20 minutes.

---

## Clock

### Block 0 — 00:00–00:30  Setup

- Compose PostGIS, Python venv, `npm create` already templated from T0.
- Alembic first migration (T1) if not generated overnight.
- **Done when:** empty API `/health` and Vite page load.

### Block 1 — 00:30–01:45  Schema + seed (T1, T2)

- Models for the P0 tables first: users, roles, states, districts, projects, parcels, owners, parcel_owners, acquisition_cases, workflow_events, workflow_stage_definitions, ml_predictions, audit_logs, compensation (for KPIs), affected_families, possession.
- Defer: dashboard_presets, notifications if time-crunched (alerts table still needed by P1).
- Run seed. Fix broken FKs immediately.
- **Done when:** SQL counts match README; a parcel has geom.

### Block 2 — 01:45–02:45  Auth (T3, T4)

- Login + JWT + require_roles.
- Seed four users.
- **Done when:** curl login works; 403 on admin route with field token.

**Frontend parallel from 01:45:** shell, Tailwind layout, login page, disclaimer, role sidebar (T10). Mock dashboard with static numbers until API is ready.

### Block 3 — 02:45–04:15  P0 APIs (T5, T6, T7, T8)

Order inside the block:

1. Parcels search + get  
2. Projects list + get  
3. Acquisition get + timeline + transition  
4. Dashboard KPIs + charts + filters  
5. GIS geojson  

Skip POST parcel/project if seed is enough; implement GET first.

- **Done when:** curl KPI JSON and one GeoJSON FeatureCollection.

### Block 4 — 04:15–05:00  ML (T9)

- Generate `train.csv` if not done in Block 1.
- `train.py` → pickle.
- Feature assembly + predict endpoint.
- **Done when:** one HIGH and one LOW case in seed predict as expected (tweak seed features if the forest disagrees — the demo must look coherent).

### Block 5 — 05:00–07:00  P0 UI (T11, T12)

- Dashboard with real API + FilterBar + Recharts.
- Parcel search + detail.
- Leaflet map + popup.
- Workflow timeline + transition modal.
- ML insights + disclaimer.

**Do not** pixel-perfect. Use Tailwind defaults, one primary colour (e.g. slate + emerald).

- **Done when:** you can run the judge script without touching Swagger.

### Block 6 — 07:00–08:30  P1 verticals (T13–T16) — timeboxed

Priority inside P1:

1. Proposal approve/reject (highest SIH visibility for R8)  
2. Field verification submit (R12 demo on a phone or responsive pane)  
3. Alerts list + evaluate button  
4. Compensation table (KPIs already show numbers from seed)

If 07:40 and (1) is not demoable, freeze P1 writes and show seed-backed read-only pages.

### Block 7 — 08:30–09:15  Integrations honesty + reports (T17, T18)

- Admin “Integrations” tab with four MOCK cards and the legal sentence.
- Reports page can reuse dashboard chart endpoints if `/api/reports` is thin.
- `demo_reset.sh` / `scripts/demo_reset.py`.

### Block 8 — 09:15–10:00  Rehearsal

Walk the **5-minute demo** (below) twice. Fix only demo-breakers (500s, empty map, login). No new features.

---

## 5-minute judging script

1. **Disclaimer** on login: synthetic data.  
2. Login `admin@demo.local` → national dashboard, filter Telangana, show delayed projects.  
3. Parcels: search a ULPIN → detail (owners, stage, compensation).  
4. Map: project layer, click parcel, status colour.  
5. Switch to `officer@demo.local` → open a case → advance stage → timeline + audit.  
6. ML insights → predict → HIGH score + synthetic-model banner.  
7. Switch to `approver@demo.local` → approve or reject a proposal (if P1 landed).  
8. Switch to `field@demo.local` on narrow viewport → GPS + photo submit (if P1 landed).  
9. Admin integrations tab: **no live government APIs**.  
10. Stop. Do not open Swagger unless asked.

---

## Cut list (if behind)

| If not done by | Cut |
|---|---|
| 04:15 | POST APIs for projects/parcels; GET only |
| 05:00 | ML evaluation.py niceties; still ship predict |
| 07:00 | Custom dashboard presets, citizen mentions |
| 07:40 | Compensation/R&R **edit**; keep read-only |
| 08:00 | Notifications table; in-app alerts only |
| 08:30 | Reports page; dashboard charts already cover R10 |
| Anytime | Redis, Celery, S3, Dockerizing the app servers, tests beyond 3 critical ones |

---

## Parallelism cheat-sheet

Frontend can work against **frozen JSON fixtures** matching API contracts until Block 3 lands, then flip `VITE_API_BASE`. Do not wait for ML to start the dashboard.

Seed data is the critical path — if seed slips, everything looks empty. Protect Block 1.
