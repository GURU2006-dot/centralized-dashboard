# SIH 26016 — Phase 4B Report

**Problem:** National Land Acquisition Management & Intelligence Platform (PS 26016)  
**Step:** Predictive delay-risk (Random Forest) + mock integration adapters  
**Date:** 2026-09-08  
**Status:** **PHASE 4B COMPLETE** for implemented and verified items below. Headed browser click-through of GIS colouring was **not** run.

Do **not** start Phase 5.

All scores, geometries, and adapter payloads are **synthetic / MOCK**. This is not a validated government decision-making model. ML does **not** approve proposals, pay compensation, or take possession.

Alembic head unchanged: `7f0736d5b557`. No destructive migration. `ml_predictions.risk_score` remains **0–1** in PostgreSQL (existing check constraint). The API displays **0–100** as `P(HIGH)×100`.

---

## 1. Status

P0 delivered and tested: synthetic dataset, RF training, reusable features, prediction service, 0–100 score, LOW/MEDIUM/HIGH, persist, case UI, dashboard KPIs, HIGH-risk alert path, regression tests, frontend build.

P1: GIS bulk GeoJSON with risk, analytics, prediction history, indicators, model page.

P2: batch predict, mock adapters, integration status/sync.

---

## 2. ML architecture

```
Acquisition case (PostgreSQL)
        ↓  services/ml_features.py  (SQL aggregates)
Feature dict (FEATURE_NAMES)
        ↓  app.ml.predictor  (no FastAPI/SQLAlchemy)
RandomForestClassifier artifact
        ↓
P(HIGH) 0–1 stored · display 0–100 · category
        ↓
ml_predictions + optional ML_HIGH_RISK alert
        ↓
API envelope → React
```

Training is offline: `python -m app.ml.train` / `python scripts/train_ml.py`. Never from a request.

---

## 3. Feature list (train = serve)

| Feature | Meaning |
|---|---|
| current_stage_index | 1–8 catalogue order |
| days_since_start | days since `started_at`/`created_at` |
| days_in_current_stage | days since `stage_entered_at` |
| workflow_event_count | count of `workflow_events` |
| completed_stage_count | index − 1 |
| remaining_stage_count | 8 − index |
| compensation_assessed | assessed INR |
| compensation_paid_ratio | paid/assessed |
| unpaid_balance | assessed − paid |
| field_verification_done | SUBMITTED/ACCEPTED |
| field_checks_complete | 0–3 flags |
| gps_available | lat/lng present |
| document_count | case or parcel docs |
| unverified_document_count | not VERIFIED |
| affected_family_count | project families |
| displaced_family_count | `is_displaced` |
| project_area_ha | estimated area |
| parcel_area_ha | parcel area |
| project_is_delayed | project status DELAYED |

No owner PII. No invented APPROVAL case stage.

---

## 4. Synthetic dataset

`app/ml/dataset.py` — **1200** rows, `numpy` generator, `seed=42`, reproducible.

Labels come from a **transparent heuristic** (long stage dwell, unpaid compensation, incomplete field work, unverified docs, displaced families, DELAYED project, remaining stages) **plus Gaussian noise**, then the same 0–39 / 40–69 / 70–100 cuts. Labels are **not** independent of features.

This is **not** DoLR/state MIS history.

---

## 5. Model configuration

`RandomForestClassifier(n_estimators=80, max_depth=8, min_samples_leaf=4, class_weight="balanced", random_state=42)`  
Stratified 80/20 split.

---

## 6. Evaluation metrics (actual training run)

From `backend/app/ml/artifacts/metrics.json`:

| Metric | Value |
|---|---|
| n_train / n_test | 960 / 240 |
| accuracy | 0.7792 |
| precision_macro | 0.669 |
| recall_macro | 0.5896 |
| f1_macro | 0.6088 |
| roc_auc_ovr | 0.866 |

Confusion matrix is stored in the metrics file. These numbers are **not** inflated.

---

## 7. Model artifact

- `backend/app/ml/artifacts/delay_risk_model.joblib`
- `backend/app/ml/artifacts/metrics.json`

---

## 8. Prediction API

| Method | Path | Who |
|---|---|---|
| POST | `/api/ml/predict/{case_id}` | ADMIN, officer, approver |
| POST | `/api/ml/predict/batch` | same |
| GET | `/api/ml/predictions/{case_id}` | any reader (scoped) |
| GET | `/api/ml/summary` | any reader |
| GET | `/api/ml/analytics` | any reader |
| GET | `/api/ml/metrics` | any reader |
| GET | `/api/gis/parcels` | any reader (bulk GeoJSON + risk) |

Envelope `{ data, meta }` with SYNTHETIC disclaimer. Field officer POST predict → **403**.

---

## 9. Database changes

**None.** Existing `ml_predictions` used: `risk_level`, `risk_score` (0–1), `features` JSONB snapshot, `model_version`, `trained_on=SYNTHETIC`, `predicted_at`, `predicted_by`.

---

## 10–11. Scoring and categories

- Stored: `risk_score = P(HIGH)` in 0–1.  
- Display: `round(P(HIGH)×100, 1)` as **Delay Risk Score / 100**.  
- Category from display: LOW 0–39, MEDIUM 40–69, HIGH 70–100. **Prototype conventions, not government standards.**  
- Not described as a calibrated probability of delay.

---

## 12. Alerts

HIGH predictions call `AlertService.emit_ml_high` (`rule_code=ML_HIGH_RISK`). Dedup: unread alert for same rule + recipient + case. Second predict on the same HIGH case returns `alerts_created: 0`.

---

## 13. Dashboard

Additional KPI cards from `/api/ml/summary`: cases scored, high/medium/low, average display score. Existing dashboard chart `risk` still uses latest stored predictions.

---

## 14. GIS

`GET /api/gis/parcels` returns a FeatureCollection (limit 80) with ULPIN, status, stage, **risk_score / risk_level**. Leaflet colours by risk, status, or stage. No N× parcel-detail fetch. Geometries are existing PostGIS polygons.

---

## 15. Analytics

`/analytics` uses `/api/ml/analytics`: risk by stage and by state from latest predictions, plus operational stage counts.

---

## 16. Integration adapters

Internal ports + **mock** implementations only (`INTEGRATION_MODE=mock`):

- `MockLandRecordsAdapter`
- `MockCadastralAdapter`
- `MockRegistrationAdapter`
- `MockFinancialAdapter`

`GET /api/integrations/status` — `mode: MOCK`, `UNAVAILABLE_PUBLIC`.  
`POST /api/integrations/{system}/lookup` — synthetic/mock DTO, badge MOCK / DEMONSTRATION.  
`POST /api/integrations/{system}/sync` — admin; **synced: 0**, does not import government data.  
External mode stubs fail closed **503** with no invented URLs.

---

## 17. Frontend changes

Updated Phase 4A SPA (no second app): dashboard ML KPIs, acquisition delay-risk panel + Run prediction + indicators + history, GIS bulk + risk layer, analytics, `/model` card, integrations status/lookup, acquisition risk filter, project risk index (mean of latest case display scores).

---

## 18. RBAC

Unchanged JWT. Predict: ADMIN / ACQUISITION_OFFICER / APPROVING_AUTHORITY. Field: view scoped cases/GIS only. Backend remains authoritative.

---

## 19–20. Tests

```
python3 scripts/demo_reset.py
cd backend && python3 -m pytest -q
→ 54 passed
```

New: `tests/test_ml.py`, `tests/test_integrations.py` (features, thresholds, reproducible dataset, train+score range, auth, 403, 404, persist, GIS FeatureCollection, mock status/lookup/sync).

---

## 21. End-to-end (Vite proxy :5173 → API :8000)

| Step | Result |
|---|---|
| Login | 200 |
| Dashboard KPIs | 8 projects |
| ML summary | 24 scored (seed) · 6 HIGH / 9 MED / 9 LOW · avg 43.7 |
| Open case + Run prediction | 200 · **3.6 / 100 LOW** · persisted |
| Second predict | `alerts_created: 0` |
| History | ≥ 1 row |
| GIS FeatureCollection | 200, 5 features |
| Metrics | f1_macro 0.6088 |
| Integrations status | mock |
| Field officer predict | 403 |
| Headed GIS colour / button click | **NOT TESTED** |

This live case was LOW so a **new** HIGH alert was not created in the E2E walk. Seed already contains HIGH rows; evaluate/dedup path is implemented and covered when category is HIGH.

---

## 22. Known limitations

1. HIGH class is rare in the synthetic set (honest metrics). Many live cases score LOW/MEDIUM.  
2. Display 0–100 vs DB 0–1 must be converted in list views (`×100`).  
3. Indicators are feature rules, not SHAP.  
4. Batch predict commits after each case’s in-memory inserts then one commit.  
5. GIS cap 80 features per request.

---

## 23. Commands

```bash
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
python ../scripts/demo_reset.py
python ../scripts/train_ml.py          # if artifact missing
uvicorn app.main:app --host 0.0.0.0 --port 8000

cd ../frontend
npm install
npm run dev
```

---

## 24. Files created / modified

**New:** `backend/app/ml/*`, `backend/app/services/ml.py`, `ml_features.py`, `gis.py`, `integrations.py`, `backend/app/integrations/*`, `backend/app/api/ml.py`, `gis.py`, `integrations.py`, `backend/tests/test_ml.py`, `test_integrations.py`, `scripts/train_ml.py`, frontend `api/ml.js`, `gis.js`, `integrations.js`.

**Updated:** `requirements.txt`, `config.py`, `api/router.py`, `api/acquisitions.py`, `repositories/acquisitions.py`, `services/alerts.py`, dashboard/GIS/acquisition/project/analytics/integrations React pages, `App.jsx`, `roles.js`, `ParcelMap.jsx`.

**Not changed:** Alembic, SQLAlchemy table DDL, JWT, proposal approval rules.

---

## 25. Phase 5 recommendation

Only if a later brief requires it: authorized historical retraining (`trained_on=AUTHORIZED_HISTORICAL` only when true), calibration, bulk GeoJSON pagination, or a real adapter against a **documented authorized** spec. Do not connect live government systems otherwise.

---

Phase 4B **STOP**.
