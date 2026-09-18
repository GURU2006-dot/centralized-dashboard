# SIH 26016 — Final test report (Phase 5)

**Date:** 2026-09-08  
**Environment:** PostgreSQL 17 + PostGIS on localhost:5432 (`nlamp`/`nlamp`/`nlamp`), FastAPI `:8000`, Vite `:5173`. Docker CLI **not installed**.  
**Reset:** `python scripts/demo_reset.py` before pytest and after the mutating API walk.

All figures below are from this run. Nothing is inflated.

---

## 1. Commands and totals

| Suite | Command | Result |
|---|---|---|
| Seed reset | `python3 scripts/demo_reset.py` | Matches EXPECTED baseline |
| Backend | `cd backend && python3 -m pytest -q` | **54 passed** |
| Production UI | `cd frontend && npm run build` | **built** (`dist/`, 1.83 s) |
| API walk | `PYTHONPATH=backend python3 scripts/phase5_validate.py` | **82 passed / 0 failed** |
| Browser | `node scripts/phase5_browser.mjs` (Playwright Chromium, headless) | **24 passed / 0 failed** |
| Docker Compose | `docker compose up` | **Not run** — no `docker` binary |

---

## 2. Seed baseline (after reset)

| Table | Count |
|---|---|
| projects | 8 |
| land_parcels | 80 |
| acquisition_cases | 60 |
| proposals | 8 |
| compensation | 32 |
| affected_families | 51 |
| rehabilitation | 17 |
| resettlement | 17 |
| possession | 16 |
| field_verifications | 8 |
| alerts | 12 |
| notifications | 8 |
| ml_predictions | 24 |
| users | 4 |

---

## 3. Pytest (54)

`tests/test_database.py`, `test_auth.py`, `test_api.py`, `test_phase3_workflow.py`, `test_ml.py`, `test_integrations.py`.

Covered: schema/seed counts, JWT login/401, RBAC, dashboard KPIs from SQL, parcel GeoJSON without owner PII, proposal approval creating cases, stage skip 400, compensation/possession gates, RF score range, field 403 on predict, GIS FeatureCollection, mock integration status/lookup/sync.

---

## 4. API walkthrough matrix (`scripts/phase5_validate.py`)

82 assertions. Highlights:

| Area | Result |
|---|---|
| Health | `/health` 200 `{status: ok}` |
| Auth | 4 roles login + `/me`; bad password 401; no token 401 |
| RBAC | Field: no project create, no proposals, no predict, no audit. Officer: 3 TG projects. Approver: no project create |
| Dashboard | 8 projects, 51 families, charts keys, no PII |
| GIS | FeatureCollection |
| Proposal | draft → edit → submit → officer 403 approve → verify → approver approve `cases_created=1` → re-approve 409; reject path |
| Workflow | SIA open; skip 400; field/approver 403 transition; SIA→…→COMPENSATION_ASSESSMENT; pay gate; possession TAKEN required for COMPLETED; CLOSED |
| Field | list assigned; officer 403; submit without GPS 400; patch GPS; photo; submit |
| Documents | upload 201; verify |
| ML | score 0–100 (example live **10.3 LOW**); raw 0–1; SYNTHETIC; seed HIGH filter ≥1 |
| Alerts | re-predict seed HIGH case → live category **LOW**; second predict `alerts_created=0` |
| Integrations | mode mock; lookup MOCK; sync 0; officer 403; unknown ULPIN 404 |

The API script **mutates** the database (extra parcel/proposal/cases, field submit). Always `demo_reset` afterwards.

---

## 5. Browser walkthrough (`scripts/phase5_browser.mjs`)

Headless Chromium against `http://127.0.0.1:5173` (Vite proxy). 24 checks:

Login page + synthetic banner; invalid credentials toast; admin dashboard KPIs; projects list + detail; parcels; GIS heading + `.leaflet-container`; proposals; acquisition list + case **Delay risk** + **Run prediction** + `/ 100`; alerts; analytics; integrations `MOCK / DEMONSTRATION`; model disclaimer; 390×844 sidebar; logout; field officer login without Proposals nav; field verification heading.

OSM raster tiles were not separately asserted (sandbox/network). Leaflet map container loaded.

Playwright was run from `/tmp/pw` (not a frontend production dependency). System Chromium libs (`libatk`) were installed on this host so the browser could launch.

---

## 6. Defects found and fixed in Phase 5

| Defect | Fix |
|---|---|
| `ModelPage` used in `App.jsx` but not imported → blank login (`ModelPage is not defined`) | Import `ModelPage` |
| Live RF displayed ~1–4 / 100 (raw `P(HIGH)×100`) so almost everything looked LOW | Class-midpoint index in `predictor.py` |
| Acquisition filter grid cramped | `md:grid-cols-2 xl:grid-cols-4` |
| Settings logout did not `navigate('/login')` | Navigate after `logout()` |
| Model card still said stored score = P(HIGH) | Copy updated |

---

## 7. Remaining limitations (not treated as silent passes)

1. **Seed HIGH ≠ live RF.** Filter `risk_level=HIGH` returns seed heuristic rows; `POST /api/ml/predict` on those cases often returns **LOW** (e.g. 10.3). Demo script states this.
2. **Docker** unavailable here. Compose file exists for PostGIS only.
3. **Document download** is local-disk metadata; do not claim authenticated remote DAM.
4. **No headed GIS colour screenshot** beyond Leaflet container + API FeatureCollection (headless walk confirmed container; colouring code is in `ParcelMap.jsx`).
5. Frontend production bundle warns chunk > 500 kB (Recharts + Leaflet). Acceptable for the prototype.
6. Approving seed `PROP-2026-007` would add ~10 cases and break the Phase 2 “60 cases” assertion. Tests use a fresh 1-parcel proposal.

---

## 8. ML metrics (training artifact, unchanged)

| Metric | Value |
|---|---|
| n_train / n_test | 960 / 240 |
| accuracy | 0.7792 |
| f1_macro | 0.6088 |
| roc_auc_ovr | 0.866 |

---

## 9. Reproduction

```bash
python scripts/demo_reset.py
cd backend && python3 -m pytest -q
cd ../frontend && npm run build
# with API + Vite running:
PYTHONPATH=backend python3 scripts/phase5_validate.py
python scripts/demo_reset.py
node scripts/phase5_browser.mjs
```
