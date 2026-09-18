# E. ML interface

**Algorithm:** Random Forest classifier (scikit-learn `RandomForestClassifier`)  
**Task:** Acquisition **delay risk** for a case — `LOW` / `MEDIUM` / `HIGH` plus probability score.  
**Isolation:** `backend/app/ml/` has **no** FastAPI or SQLAlchemy imports. FastAPI talks to it only through `services/ml_service.py`.

**Disclaimer (API + UI, always):**

> This model is trained on **synthetic demonstration data**. It is **not** trained on real government historical land-acquisition records.

---

## 1. Module files

```
backend/app/ml/
  features.py          # FEATURE_NAMES ordered list — the contract
  preprocessing.py     # DataFrame → numeric matrix
  train.py             # CLI/script entry: CSV → model.pkl + metrics.json
  predict.py           # load pickle, predict one row
  evaluation.py        # accuracy, f1, confusion (used by train)
  artifacts/
    model.pkl
    metrics.json
```

`scripts/train_ml.py` is a thin wrapper so training is not started from a router.

---

## 2. Feature contract

Order is fixed. Training CSV columns **and** live feature dict **must** use these names.

| Feature | Type | Source at inference | Meaning |
|---|---|---|---|
| `sia_duration_days` | float | days in stage `SIA` (0 if not entered) | SIA dwell time |
| `approval_delay_days` | float | max(0, dwell in APPROVAL − expected) | Overrun on approval |
| `document_issue_count` | int | documents on case/parcel with `REJECTED` or missing required types | Paperwork friction |
| `dispute_count` | int | cases/parcels with `DISPUTED` or compensation `DISPUTED` | Conflict load |
| `affected_family_count` | int | families on project (or parcel if linked) | Social complexity |
| `owner_count` | int | `COUNT(parcel_owners)` | Title complexity |
| `compensation_pending_days` | float | days since assessment if not fully paid, else 0 | Payment lag |
| `project_area_ha` | float | `projects.estimated_area_ha` | Scale |
| `current_stage_index` | int | `sequence_order` of current stage (1–12) | How far along |
| `previous_processing_delay_days` | float | sum of historical stage overruns on this case | Habitual delay |

No free-text, no PII. Owner **count** only.

Optional (keep out of v1 unless training CSV already has them): `state_code` one-hot — **rejected for v1** to keep the forest tiny and avoid leaking geography as fake causality.

---

## 3. Training input

**File:** `data/ml/train.csv` (SYNTHETIC)

```
sia_duration_days,approval_delay_days,document_issue_count,dispute_count,
affected_family_count,owner_count,compensation_pending_days,project_area_ha,
current_stage_index,previous_processing_delay_days,delay_risk
```

`delay_risk` ∈ {`LOW`,`MEDIUM`,`HIGH`} — the label.

**Generation rules (documented in `data/README.md`):**

- ~800–1500 rows, class-balanced enough for a demo forest.
- Labels derived from a transparent heuristic **plus noise**, e.g. HIGH if `previous_processing_delay_days > 30` or `dispute_count >= 2`, so the live demo “makes sense” when a disputed case scores HIGH.
- File header comment / README: **SYNTHETIC. Not DoLR/state MIS extracts.**

**`train.py` behaviour:**

1. Load CSV.
2. `preprocessing.fit_transform` (SimpleImputer median + optional StandardScaler; RF does not need scaling — **skip scaler** to keep pickle simple).
3. `RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, class_weight="balanced")`.
4. Stratified 80/20 split.
5. `evaluation.py` writes `artifacts/metrics.json` (`accuracy`, `f1_macro`, `confusion_matrix`, `n_train`, `n_test`, `trained_on: "SYNTHETIC"`, `trained_at`).
6. Joblib dump `artifacts/model.pkl`.
7. Never called from a request path.

**Replace-later path:** drop a new CSV with the **same columns** (authorized historical data) and re-run `train.py`. Change `trained_on` in metrics to `AUTHORIZED_HISTORICAL` only when that is actually true.

---

## 4. Prediction input

`predict.py` accepts a `dict[str, float|int]` with the 10 feature names.

`ml_service.predict_for_case(case_id)`:

1. Load case + related rows.
2. Compute the 10 features (pure Python, SQL aggregates).
3. Call `ml.predict.predict(features)`.
4. Persist `ml_predictions`.
5. Return DTO.

If the router sends a raw `features` object (demo/test), skip SQL assembly; still stamp `trained_on=SYNTHETIC`.

---

## 5. Prediction output

Internal (from `predict.py`):

```python
{
  "risk_level": "HIGH",      # argmax class
  "risk_score": 0.78,        # P(class=HIGH) if HIGH else P(predicted class)
  "class_probabilities": { "LOW": 0.07, "MEDIUM": 0.15, "HIGH": 0.78 },
  "model_version": "rf-delay-v1",
  "trained_on": "SYNTHETIC"
}
```

**Score definition (fixed):** `risk_score = P(HIGH)` always, so charts sort consistently. `risk_level` from thresholds:

| P(HIGH) | risk_level |
|---|---|
| `< 0.33` | LOW |
| `0.33–0.66` | MEDIUM |
| `> 0.66` | HIGH |

Thresholds live in `features.py` / `predict.py` constants so they can be tuned without touching routers.

HTTP mapping: `POST /api/ml/predict-delay` as specified in API contracts.

---

## 6. Model storage

| Artifact | Path | Git |
|---|---|---|
| Pickle | `backend/app/ml/artifacts/model.pkl` | optional; regenerate in setup |
| Metrics | `backend/app/ml/artifacts/metrics.json` | yes, for demo slide |
| Training CSV | `data/ml/train.csv` | yes |

Load once at process start (`predict.load_model()`), cache in module global. If missing → API 503 `MODEL_NOT_LOADED` (setup script should have trained it).

**No** MLflow, **no** model registry, **no** GPU.

---

## 7. API boundary

```
Router  POST /api/ml/predict-delay
   ↓  Pydantic PredictDelayRequest
ml_service.py
   ↓  assemble features from DB  (or trust request.features)
app.ml.predict.predict(feature_dict)
   ↓  dict
ml_service persists ml_predictions
   ↓  if risk_level == HIGH → alert_service.create(ML_HIGH_RISK)
Router  PredictDelayResponse + disclaimer
```

**Forbidden:** routers importing sklearn; `train.py` importing FastAPI; training inside a request.

---

## 8. Evaluation (offline only)

`evaluation.py` returns:

- accuracy, macro-F1
- confusion matrix 3×3
- feature_importances_ mapped to `FEATURE_NAMES`

Shown on MlInsightsPage as a small “model card” with the synthetic disclaimer. Not a live metrics pipeline.

---

## 9. What we are not building

- Regression of delay days (classification is enough for the demo).
- SHAP explanations (nice-to-have P2; skip).
- Auto-retrain on new cases.
- Using ML for compensation amounts or title fraud.
