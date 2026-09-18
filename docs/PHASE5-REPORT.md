# SIH 26016 — Phase 5 report

**Problem:** National Land Acquisition Management & Intelligence Platform (PS 26016)  
**Step:** Final integration, validation, SIH demo readiness  
**Date:** 2026-09-08  

**READY FOR SIH DEMO**

All projects, parcels, owners, geometries, compensation figures, and ML scores are **synthetic demonstration data**. Integrations are **MOCK**. The delay-risk forest is **not** a validated government decision-making model.

---

## 1. What Phase 5 did

Inspected the frozen stack (Alembic `7f0736d5b557`, `INTEGRATION_MODE=mock`, no live gov APIs). Did **not** add Kafka, Redis, LLMs, or live adapters.

Validated:

- Browser (Playwright Chromium vs Vite `:5173`) — 24/24
- API walk (`scripts/phase5_validate.py`) — 82/82
- Backend pytest — 54/54
- `python scripts/demo_reset.py` — deterministic EXPECTED counts
- `npm run build` — production frontend bundle
- Docker — **unavailable** in this environment (documented, not redesigned)

Fixed only demonstrated defects (see §3). Wrote [DEMO-SCRIPT.md](./DEMO-SCRIPT.md), [FINAL-ARCHITECTURE.md](./FINAL-ARCHITECTURE.md), [FINAL-TEST-REPORT.md](./FINAL-TEST-REPORT.md).

---

## 2. Demo path (verified)

| Step | Result |
|---|---|
| Login 4 roles | 200; bad password 401 |
| Dashboard KPIs | 8 projects, 51 families, SQL-backed charts |
| GIS | FeatureCollection + Leaflet container; colour modes in UI |
| Proposal | Officer cannot approve (403); approver APPROVED creates cases; re-approve 409; reject creates none |
| Workflow | Skip 400; compensation/possession gates; COMPLETED → CLOSED |
| ML | 0–100 display, 0–1 stored, SYNTHETIC disclaimer, field 403 |
| Alerts | HIGH path implemented; unread dedup; live RF often LOW on seed HIGH |
| Field | GPS required; no invented coordinates; mobile nav |
| Integrations | MOCK badge; sync 0 |
| Logout | Header + settings |

Password `Demo@1234` is **not** hard-coded in frontend source. Demo directory emails are listed on the login card.

---

## 3. Defects fixed

1. **Blank app:** `ModelPage` referenced without import — login never hydrated.
2. **Unusable live scores:** `P(HIGH)×100` ≈ 1–4. Predictor now stores/displays the class-midpoint index `(0·P_LOW + 50·P_MED + 100·P_HIGH)`.
3. Acquisition filter layout on mid-width screens.
4. Settings logout now navigates to `/login`.
5. Model-card copy no longer claims stored score = P(HIGH).

---

## 4. Tests (this run)

```
python3 scripts/demo_reset.py          # EXPECTED counts match
cd backend && python3 -m pytest -q     # 54 passed
cd frontend && npm run build           # ok
PYTHONPATH=backend python3 scripts/phase5_validate.py  # 82 passed
node scripts/phase5_browser.mjs        # 24 passed
python3 scripts/demo_reset.py          # restore after API mutation
```

Docker Compose was **not** executed (`docker` missing). `docker-compose.yml` still describes PostGIS only.

---

## 5. Limitations judges should hear

- Seed **HIGH** alerts/scores are seed heuristics; **live RF** on the same cases is often **LOW/MEDIUM**.
- No live cadastral / DoLR / registration / financial APIs.
- OSM is a basemap, not a cadastral layer.
- Document store is local disk.
- Do not approve seed `PROP-2026-007` during the slot (10 extra cases).

---

## 6. How to run the demo

See [DEMO-SCRIPT.md](./DEMO-SCRIPT.md). Short form:

```bash
python scripts/demo_reset.py
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

Open `http://127.0.0.1:5173` — `admin@demo.local` / `Demo@1234`.

---

## 7. Stop

Phase 5 is complete. No Phase 6 work from this brief.

**READY FOR SIH DEMO**
