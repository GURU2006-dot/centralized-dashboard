# SIH 26016 — Phase 3 Report

**Problem:** National Land Acquisition Management & Intelligence Platform (PS 26016)  
**Step:** Workflow mutations — proposals, case transitions, compensation, possession, R&R, field, documents, alerts  
**Date:** 2026-09-08  
**Status:** **Complete.** Stop here. Phase 4 (React / ML / live government APIs) has **not** been started.

All API data is **synthetic demonstration data**. It is not live land records, cadastral maps, or government statistics.

Phase 1 database schema and Phase 2 JWT/RBAC envelopes were **not redesigned**. Alembic head remains `7f0736d5b557`.

---

## IMPLEMENTED

| Item | Notes |
|---|---|
| Proposal CRUD | `POST/GET/PATCH /api/proposals` — DRAFT only for edit |
| Proposal submit / verify | Officer/admin; `DRAFT → SUBMITTED → UNDER_VERIFICATION` |
| Proposal approve / reject | Approver/admin only; reject requires remarks |
| Approval creates cases | Same transaction; cases start at **SIA**; `workflow_events` row with `from_stage=null` |
| Unique `(project, parcel)` | Existing case is linked, not duplicated (`cases_already_present`) |
| Case transition | `POST /api/acquisitions/{id}/transition` — sequential catalogue only |
| Append-only events | New `workflow_events` row per transition; timeline unchanged from Phase 2 |
| Compensation | GET/POST/PATCH; paid cannot exceed assessed |
| Possession | GET/POST/PATCH (`NOT_TAKEN` / `PARTIAL` / `TAKEN`) |
| Rehabilitation / resettlement | List by case; POST/PATCH records |
| Affected families | List/get/create/patch; **no contact / PII** in responses |
| Field verification | Assigned parcels only; GPS + three checks required to submit; photo upload |
| Documents | Local files under `data/uploads` + PostgreSQL row; pdf/jpeg/png/webp, 10 MiB |
| Alerts | `POST /api/alerts/evaluate` (admin); unread + recipient dedup |
| Notifications | List, mark one, mark all |
| Audit log | Admin list of append-only `audit_logs` |
| Layers | Routers → services → repositories / SQLAlchemy |
| Envelope / JWT / RBAC | Unchanged from Phase 2 |

**Proposal statuses (only these):** `DRAFT`, `SUBMITTED`, `UNDER_VERIFICATION`, `APPROVED`, `REJECTED`.  
SIA is a **case stage**, not a proposal status.

**Case stages (catalogue, frozen):**  
`SIA → NOTIFICATION → AWARD → COMPENSATION_ASSESSMENT → COMPENSATION_PAID → POSSESSION → REHABILITATION_RESETTLEMENT → COMPLETED`  
Alias: request body `R_AND_R` normalizes to `REHABILITATION_RESETTLEMENT`. There is no second case-level approve.

**Gates**

- `COMPENSATION_PAID` requires assessed amount `> 0` and paid `≥` assessed.
- `COMPLETED` requires possession status `TAKEN`.
- Field officers and approving authority **cannot** transition cases (HTTP 403).
- Illegal skip → HTTP 400 `ILLEGAL_TRANSITION`. Already approved/rejected/submitted-again → HTTP 409.

---

## TESTED

### Automated

```
python3 /home/user/scripts/demo_reset.py
cd backend && python3 -m pytest -q
→ 45 passed
```

Breakdown: Phase 1 DB (14) + Phase 2 API/auth (24) + Phase 3 workflow (7) = **45**.

Phase 3 tests (`backend/tests/test_phase3_workflow.py`):

- Draft create/edit; submit without parcels → 400; edit after submit → 409; field officer cannot list proposals → 403
- Reject without remarks → 422; reject → `REJECTED`; re-reject → 409
- Officer cannot approve → 403; approve of a **new 1-parcel** (not seed `PROP-2026-007`) creates **1** case at SIA + timeline event; re-approve → 409
- Skip stage → 400 `ILLEGAL_TRANSITION`; field/approver transition → 403; sequential `SIA → NOTIFICATION` + append-only event
- Compensation paid > assessed → 400; negative amount → 422
- Possession create/patch; rehab/resettlement GET; families list
- Field GPS incomplete submit → 400; photo PNG; submit → `SUBMITTED`; re-submit → 409; officer cannot list field rows → 403
- Alert evaluate; mark read; notifications; audit admin-only

**Do not approve seed `PROP-2026-007` (TH-TG-SEZ, 10 parcels).** Tests insert a dedicated parcel so Phase 2 `total == 60` still holds **if the suite starts from a reset database**. After Phase 3 tests/E2E, case count is higher; run `demo_reset` before asserting seed totals.

### Manual E2E (live Uvicorn `:8000`)

32 checks, 0 failures, including:

| Check | Result |
|---|---|
| `/health`, `/docs`, `/redoc` | 200 |
| Create → submit → verify → officer 403 → approver approve | 1 case created |
| Field/approver cannot transition | 403 |
| Skip `SIA → AWARD` | 400 `ILLEGAL_TRANSITION` |
| `SIA → NOTIFICATION` + timeline length 2 | 200 |
| `COMPENSATION_PAID` without full payment | 400 `VALIDATION_ERROR` |
| GET compensation / possession / rehab / resettlement | 200 |
| Families JSON has no `contact` | Pass |
| Document upload + verify | 201 / 200 |
| Field list (8 assigned); officer 403 | Pass |
| Alerts evaluate (dedup on second call in pytest) | Pass |
| Notifications + audit; field audit 403 | Pass |
| Seed `PROP-2026-007` not approved | Pass |

Demo logins (password `Demo@1234`): `admin@demo.local`, `officer@demo.local`, `approver@demo.local`, `field@demo.local`.

---

## NOT TESTED

| Item | Why |
|---|---|
| Full 8-stage walk of one case to `COMPLETED` | Only first sequential step + compensation gate were exercised end-to-end |
| `R_AND_R` alias on a live request | Implemented in `normalize_stage`; not sent in E2E |
| Binary file **download** endpoint | Upload + metadata GET only; bytes stay on disk |
| Duplicate-alert storm under concurrent evaluate | Sequential evaluate only |
| Officer scoped to a non-TG case mutation | Officer create of MH compensation would 404 by design; not asserted as its own test |
| React UI, ML train/predict, live government APIs | Out of this phase |

---

## BLOCKED

None for Phase 3 scope. Docker Compose remains unused in this environment (`policy-rc.d`); local PostgreSQL 17 + PostGIS is the runtime.

---

## Architecture (unchanged)

```
React (not built)
    │  REST JSON envelope
    ▼
FastAPI  JWT + RBAC
    ▼
Services (proposals, workflow engine, compensation, …)
    ▼
Repositories / SQLAlchemy
    ▼
PostgreSQL 16/17 + PostGIS   (Alembic 7f0736d5b557)
```

Errors:

```json
{ "error": { "code": "ILLEGAL_TRANSITION", "message": "...", "details": {} } }
```

Success still includes `meta.data_source = SYNTHETIC`.

---

## Files in this step

**New**

- `backend/app/workflow/stages.py`, `backend/app/workflow/engine.py`
- `backend/app/services/proposals.py`, `audit.py`, `notifications.py`, `alerts.py`, `compensation.py`, `possession.py`, `rr.py`, `families.py`, `field_verification.py`, `documents.py`
- `backend/app/schemas/workflow.py`
- `backend/app/api/proposals.py`, `compensation.py`, `possession.py`, `rehabilitation.py`, `resettlement.py`, `families.py`, `field_verification.py`, `documents.py`, `alerts.py`, `notifications.py`, `audit.py`
- `backend/tests/test_phase3_workflow.py`

**Updated**

- `backend/app/api/router.py`, `backend/app/api/acquisitions.py` (transition)
- `backend/app/deps.py` (ProposalWriter/Reader, Approver, OfficerOps, FieldOps, AdminOnly)
- `backend/app/config.py` (`UPLOAD_DIR`, `MAX_UPLOAD_BYTES`)
- `backend/app/repositories/users.py` (`list_by_role`)
- `backend/requirements.txt` (`python-multipart`)

**Not changed:** Alembic migration, SQLAlchemy models, Phase 2 auth/dashboard/projects/parcels read APIs.

---

## Endpoints added (all under `/api`, JWT)

| Method | Path | Who |
|---|---|---|
| POST/GET/PATCH | `/proposals`, `/proposals/{id}` | Officer/admin write; approver can read |
| POST | `/proposals/{id}/submit`, `/verify` | Officer/admin |
| POST | `/proposals/{id}/approve`, `/reject` | Approver/admin |
| POST | `/acquisitions/{id}/transition` | Officer/admin |
| GET/POST/PATCH | `/compensation`, `/compensation/{case_id}` | Read: any reader; write: officer/admin |
| GET/POST/PATCH | `/possession`, `/possession/{case_id}` | Same |
| GET/POST/PATCH | `/rehabilitation`, `/resettlement` | Same |
| GET/POST/PATCH | `/families`, `/families/{id}` | Same |
| GET/PATCH | `/field-verification`, `/{id}` | Field/admin |
| POST | `/field-verification/{id}/photos`, `/submit` | Field/admin |
| GET/POST/PATCH | `/documents`, `/documents/{id}` | Write: officer/admin |
| GET/POST | `/alerts`, `/alerts/evaluate` | Evaluate: admin |
| PATCH | `/alerts/{id}/read` | Recipient or admin |
| GET/PATCH | `/notifications`, `/read-all`, `/{id}/read` | Authenticated user |
| GET | `/audit` | Admin |

---

## How to run

```bash
# local Postgres: user/db/password nlamp
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
python ../scripts/demo_reset.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
python -m pytest -q
```

Reseed before any test that asserts **60** acquisition cases.

---

## Explicitly out of this step

- React / glass UI  
- ML train or predict  
- Live cadastral / DoLR / government APIs (adapters remain MOCK / unused)  
- Schema redesign, second approval on cases, `R_AND_R` as a stored stage code  
- Owner ID numbers, phones, addresses in general APIs  

---

## Known limitations

1. Uploaded files are stored on local disk; there is no authenticated binary download route.  
2. `workflow_events` are append-only — leftover cases from tests cannot be fully erased without `demo_reset`.  
3. Default `JWT_SECRET_KEY` is for development only.  
4. Alert evaluate is on-demand (`POST /api/alerts/evaluate`), not a background scheduler.

---

## Next step (not started)

**Phase 4** would be a frontend or ML/adapters — only if a later brief says so. Phase 3 stops here.
