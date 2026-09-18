# SIH 26016 — 8-minute demo script

**All data is SYNTHETIC.** Integrations are MOCK. The Random Forest is a prototype trained on a synthetic dataset and is **not** a validated government decision-making model. Predictions must not automatically approve land, pay compensation, or take possession.

Password for every demo account: `Demo@1234` (not stored in frontend source).

| Email | Role | Use |
|---|---|---|
| `admin@demo.local` | ADMIN | National dashboard, integrations, audit, ML |
| `officer@demo.local` | ACQUISITION_OFFICER | Telangana projects, proposals, transitions |
| `approver@demo.local` | APPROVING_AUTHORITY | Approve / reject only |
| `field@demo.local` | FIELD_OFFICER | Assigned parcels, GPS, photos |

Reset before the slot: `python scripts/demo_reset.py`

Do **not** approve seed draft `PROP-2026-007` (TH-TG-SEZ, 10 parcels) — it would spawn extra cases. Create a 1-parcel proposal if you need a live approval.

---

## 0. Start (30 s)

```bash
# PostgreSQL 16/17 + PostGIS on localhost:5432, db/user/password nlamp
python scripts/demo_reset.py
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
cd frontend && npm run dev   # http://127.0.0.1:5173  (proxies /api → :8000)
```

Banner on every page: synthetic demonstration data.

---

## 1. Login + dashboard (1 min) — ADMIN

1. Open `/login`. Invalid password → toast, stay on login.
2. Sign in as `admin@demo.local`.
3. Command dashboard: **8 projects**, **51 families**, compensation assessed vs paid, stage bars, risk pie.
4. Point at the amber banner. Say: these are not live cadastral or DoLR statistics.

---

## 2. GIS (1 min)

1. **GIS Map**. Leaflet + one `GET /api/gis/parcels` FeatureCollection (cap 80).
2. Colour by **Risk** (LOW teal / MEDIUM amber / HIGH red), then Status, then Stage.
3. Click a polygon → popup (ULPIN, khasra, village, risk) → case or parcel page.
4. OSM tiles are a **basemap only**, not cadastral maps. If tiles fail, polygons still draw.

---

## 3. Proposal approval (2 min) — officer then approver

**Sole approval action is `proposals.status`.** Cases have no approve button.

1. Log in as `officer@demo.local`. Sidebar is Telangana-scoped (3 projects).
2. **Proposals → New proposal**. Pick TH-TG-SEZ and **one unused parcel** (not the seed 10). Save draft → Submit → Verify.
3. Officer **Approve** → 403. Log out.
4. `approver@demo.local` → open the proposal → **Approve**. API returns `cases_created: 1`. Re-approve → 409.
5. **Acquisition Cases**: new case opens at **SIA**, status OPEN.

Narrate: reject is available instead of approve; rejected proposals create **zero** cases.

---

## 4. Workflow + compensation (1.5 min) — ADMIN or officer

On the new case:

1. Attempt skip SIA → AWARD → **400**.
2. Advance SIA → NOTIFICATION → AWARD → COMPENSATION_ASSESSMENT (remarks required by the engine).
3. COMPENSATION_PAID without a paid record → **400**.
4. Create compensation, pay full assessed amount, then COMPENSATION_PAID → POSSESSION → REHABILITATION_RESETTLEMENT.
5. COMPLETED without possession TAKEN → **400**. Create possession TAKEN, then COMPLETED → case **CLOSED**.
6. Timeline lists append-only `workflow_events`.

Approver and field officer cannot transition (403).

---

## 5. Delay-risk ML (1 min)

1. Open any acquisition case → **Delay risk**.
2. **Run prediction**. Score is **0–100** (stored 0–1). Categories: LOW 0–39, MEDIUM 40–69, HIGH 70–100 (**prototype cuts**).
3. Indicators are feature observations (days in stage, unpaid compensation, …), **not SHAP / causes**.
4. Second click on a HIGH case does not spam unread `ML_HIGH_RISK` alerts (`alerts_created: 0`).
5. **Model information**: accuracy 0.7792, f1_macro 0.6088, roc_auc_ovr 0.866, `trained_on=SYNTHETIC`.

Honest note: **seed HIGH rows are seed heuristics**. Live RF often scores the same cases **LOW/MEDIUM** because P(HIGH) is small on this synthetic model. Do not claim the forest “confirms” seed HIGH.

Field officer **Run prediction** is hidden; API 403.

---

## 6. Field verification, mobile (1 min)

1. Narrow the window or use a phone. `field@demo.local`.
2. No Proposals / Integrations / Audit in the nav. Open menu → **Field Verification**.
3. Open a record. **Capture GPS** uses the browser; if permission fails the UI **does not invent coordinates**. Submit without GPS → 400.
4. Checkboxes, photo upload to **local disk**, Submit.

---

## 7. Integrations MOCK (30 s) — ADMIN

1. **Integrations**. Each card: `MOCK / DEMONSTRATION`.
2. Lookup a real seeded ULPIN → mock DTO, `mode: MOCK`.
3. Mock sync → `synced: 0` (does not import government data).
4. Officer sync → 403.

---

## 8. Close

Log out (header icon). Repeat login as another role if judges ask.

If anything looks off: `python scripts/demo_reset.py` and refresh.
