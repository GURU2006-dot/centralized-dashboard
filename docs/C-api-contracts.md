# C. API contracts

**Base URL:** `/api`  
**Format:** JSON (`application/json`) unless noted (multipart uploads).  
**Auth:** `Authorization: Bearer <jwt>` except `POST /api/auth/login`.  
**Common headers:** `Content-Type: application/json`

## Envelope

Success (single):

```json
{ "data": { }, "meta": { "data_source": "SYNTHETIC" } }
```

Success (list):

```json
{
  "data": [ ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 0,
    "data_source": "SYNTHETIC"
  }
}
```

Error (all 4xx/5xx):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable",
    "details": [ { "field": "ulpin", "issue": "required" } ]
  }
}
```

| HTTP | When | `error.code` examples |
|---|---|---|
| 400 | Bad body / illegal workflow transition | `VALIDATION_ERROR`, `ILLEGAL_TRANSITION` |
| 401 | Missing/expired/invalid JWT | `UNAUTHORIZED` |
| 403 | Authenticated but role/scope mismatch | `FORBIDDEN` |
| 404 | Unknown id | `NOT_FOUND` |
| 409 | Unique conflict (ULPIN, case already exists) | `CONFLICT` |
| 422 | Pydantic validation | `VALIDATION_ERROR` |
| 503 | External adapter configured but unavailable | `INTEGRATION_UNAVAILABLE` |

`meta.data_source` is always present on GIS, parcel, integration, and ML payloads.

---

## Shared query filters

Used by dashboard, projects, parcels, acquisitions, reports, GIS:

| Query | Type |
|---|---|
| `state_code` | string |
| `district_code` | string |
| `project_id` | uuid |
| `stage` | workflow code |
| `status` | string |
| `date_from` `date_to` | ISO date |
| `q` | free text |
| `page` `page_size` | int, page_size max 100 |

---

## 1. Auth — `/api/auth`

### `POST /api/auth/login`

- **Auth:** public  
- **Role:** —  
- **Request:** `{ "email": "string", "password": "string" }`  
- **Response 200:**

```json
{
  "data": {
    "access_token": "jwt",
    "token_type": "bearer",
    "expires_in": 28800,
    "user": {
      "id": "uuid",
      "email": "admin@demo.local",
      "full_name": "National Admin",
      "role": "ADMIN",
      "state_code": null,
      "district_code": null
    }
  }
}
```

- **Errors:** 401 `INVALID_CREDENTIALS`; 403 if `is_active=false` (`ACCOUNT_DISABLED`)

### `GET /api/auth/me`

- **Auth:** required  
- **Role:** any  
- **Response 200:** `{ "data": { /* user as above */ } }`  
- **Errors:** 401

### `POST /api/auth/logout`

- **Auth:** required  
- **Role:** any  
- **Request:** empty  
- **Response 204**  
- **Note:** Prototype is stateless JWT; client discards token. Endpoint exists for UI symmetry.

---

## 2. Users (admin) — `/api/users`

### `GET /api/users`

- **Auth:** required · **Role:** `ADMIN`  
- **Query:** `role`, `q`, `page`  
- **Response 200:** paginated users (no `hashed_password`)  
- **Errors:** 401, 403

### `POST /api/users`

- **Auth:** required · **Role:** `ADMIN`  
- **Request:** `{ "email", "password", "full_name", "role": "FIELD_OFFICER", "state_code", "district_code" }`  
- **Response 201:** user  
- **Errors:** 409 email taken; 422

### `PATCH /api/users/{id}`

- **Auth:** required · **Role:** `ADMIN`  
- **Request:** any subset including `is_active`, `role`  
- **Response 200**  
- **Audit:** `USER_ROLE_CHANGED` / `USER_UPDATED`  
- **Errors:** 404, 403

---

## 3. Dashboard — `/api/dashboard`

### `GET /api/dashboard/kpis`

- **Auth:** required · **Role:** any authenticated (scoped: officers see their state if `user.state_code` set; admin sees all)  
- **Query:** shared filters  
- **Response 200:**

```json
{
  "data": {
    "total_projects": 8,
    "area_notified_ha": 1240.5,
    "area_acquired_ha": 810.2,
    "compensation_assessed_inr": 1520000000,
    "compensation_paid_inr": 980000000,
    "affected_families": 640,
    "displaced_families": 210,
    "possession": { "NOT_TAKEN": 40, "PARTIAL": 12, "TAKEN": 28 },
    "rr_status": { "NOT_STARTED": 30, "IN_PROGRESS": 22, "COMPLETED": 18 },
    "delayed_projects": 2,
    "timeline_adherence_pct": 72.5
  },
  "meta": { "filters_applied": {}, "data_source": "SYNTHETIC" }
}
```

### `GET /api/dashboard/charts`

- **Auth:** required · **Role:** any  
- **Query:** shared filters + `types=state,district,progress,stage,compensation,rr,timeline`  
- **Response 200:**

```json
{
  "data": {
    "state_wise_acquisition": [ { "state_code": "TG", "area_acquired_ha": 120 } ],
    "district_wise_acquisition": [ { "district_code": "TG-HYD", "area_acquired_ha": 40 } ],
    "project_progress": [ { "project_id": "uuid", "name": "", "pct_acquired": 55 } ],
    "stage_distribution": [ { "stage": "AWARD", "count": 12 } ],
    "compensation_status": [ { "status": "PAID", "amount_inr": 1 } ],
    "rr_status": [ { "status": "COMPLETED", "count": 10 } ],
    "timeline_adherence": [ { "project_id": "uuid", "on_time": true, "delay_days": 0 } ]
  }
}
```

### `GET /api/dashboard/filters`

- **Auth:** required · **Role:** any  
- **Response 200:** `{ "data": { "states": [], "districts": [], "projects": [], "stages": [], "statuses": [] } }`

---

## 4. Projects — `/api/projects`

### `GET /api/projects`

- **Auth:** required · **Role:** any  
- **Query:** shared filters + `q`  
- **Response 200:** paginated project summaries (code, name, state, status, stage, area, delayed flag)

### `POST /api/projects`

- **Auth:** required · **Role:** `ADMIN`, `ACQUISITION_OFFICER`  
- **Request:** `{ "code", "name", "purpose", "requiring_body", "state_code", "district_code", "estimated_area_ha", "estimated_compensation_inr", "start_date", "expected_end_date" }`  
- **Response 201**  
- **Audit:** `PROJECT_CREATED`  
- **Errors:** 409 duplicate code

### `GET /api/projects/{id}`

- **Auth:** required · **Role:** any  
- **Response 200:** project + KPI slice + parcel_count + case_count  
- **Errors:** 404

### `PATCH /api/projects/{id}`

- **Auth:** required · **Role:** `ADMIN`, `ACQUISITION_OFFICER`  
- **Request:** mutable fields (not `data_source`)  
- **Response 200**  
- **Audit:** `PROJECT_UPDATED`

---

## 5. Parcels — `/api/parcels`

### `GET /api/parcels`

- **Auth:** required · **Role:** any  
- **Query:** `ulpin`, `khasra`, `owner` (ILIKE), `state_code`, `district_code`, `project_id`, `status`, `stage`, `page`  
- **Response 200:** list of parcel summaries (ulpin, khasra, village, area_ha, owners_preview, status, stage, project_code, data_source)

### `GET /api/parcels/{id}`

- **Auth:** required · **Role:** any  
- **Response 200:**

```json
{
  "data": {
    "id": "uuid",
    "ulpin": "00000000000000",
    "khasra_number": "12/3",
    "owners": [ { "name": "", "share_pct": 50, "ownership_type": "JOINT" } ],
    "area_ha": 1.25,
    "state_code": "TG",
    "district_code": "TG-RR",
    "village": "",
    "location": { "lat": 17.38, "lng": 78.48 },
    "geometry": { "type": "MultiPolygon", "coordinates": [] },
    "project": { "id": "uuid", "code": "", "name": "" },
    "current_stage": "VERIFICATION",
    "acquisition_status": "IN_PROCESS",
    "compensation": { "assessed_amount_inr": 0, "paid_amount_inr": 0, "status": "NOT_ASSESSED" },
    "possession": { "status": "NOT_TAKEN" },
    "rr": { "families": 2, "displaced": 1 },
    "documents": [ { "id": "uuid", "name": "", "doc_type": "LAND_RECORD", "verification_status": "PENDING" } ],
    "data_source": "SYNTHETIC"
  }
}
```

### `POST /api/parcels`

- **Auth:** required · **Role:** `ADMIN`, `ACQUISITION_OFFICER`  
- **Request:** ulpin, khasra, state/district, area_ha, optional geometry GeoJSON, optional owner ids  
- **Response 201**  
- **Errors:** 409 duplicate ULPIN

### `PATCH /api/parcels/{id}`

- **Auth:** required · **Role:** `ADMIN`, `ACQUISITION_OFFICER`  
- **Audit:** `PARCEL_UPDATED`

---

## 6. Proposals — `/api/proposals`

### `GET /api/proposals`

- **Auth:** required · **Role:** `ADMIN`, `ACQUISITION_OFFICER`, `APPROVING_AUTHORITY`  
- **Query:** `status`, `project_id`, `page`  
- **Response 200:** list

### `POST /api/proposals`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`  
- **Request:**

```json
{
  "project_id": "uuid",
  "parcel_ids": ["uuid"],
  "required_area_ha": 12.5,
  "purpose": "NH widening",
  "estimated_compensation_inr": 50000000,
  "affected_families_count": 18,
  "proposed_start": "2026-10-01",
  "proposed_end": "2027-03-31"
}
```

- **Response 201:** proposal `status=DRAFT`  
- **Audit:** `PROPOSAL_CREATED`

### `GET /api/proposals/{id}`

- **Auth:** required · **Role:** officer / authority / admin  
- **Response 200:** proposal + parcels + documents

### `PATCH /api/proposals/{id}`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER` (owner) while `DRAFT`  
- **Errors:** 409 if not DRAFT

### `POST /api/proposals/{id}/submit`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`  
- **Request:** `{ "remarks": "optional" }`  
- **Response 200:** `status=SUBMITTED`  
- **Audit:** `PROPOSAL_SUBMITTED`  
- **Errors:** 409 if not DRAFT

### `POST /api/proposals/{id}/verify`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`, `APPROVING_AUTHORITY`  
- **Request:** `{ "remarks": "" }`  
- **Response 200:** `UNDER_VERIFICATION`

### `POST /api/proposals/{id}/approve`

- **Auth:** required · **Role:** `APPROVING_AUTHORITY`  
- **Request:** `{ "remarks": "" }`  
- **Response 200:** `APPROVED`; creates `acquisition_cases` for listed parcels if missing  
- **Audit:** `PROPOSAL_APPROVED`

### `POST /api/proposals/{id}/reject`

- **Auth:** required · **Role:** `APPROVING_AUTHORITY`  
- **Request:** `{ "remarks": "mandatory" }`  
- **Response 200:** `REJECTED`  
- **Errors:** 400 if remarks empty  
- **Audit:** `PROPOSAL_REJECTED`

---

## 7. Acquisitions — `/api/acquisitions`

### `GET /api/acquisitions`

- **Auth:** required · **Role:** any except field officer sees assigned parcels only  
- **Query:** shared filters + `parcel_id`  
- **Response 200:** case summaries

### `GET /api/acquisitions/{id}`

- **Auth:** required · **Role:** any (scoped)  
- **Response 200:** case + parcel + project + current stage + compensation + possession + latest ML prediction

### `GET /api/acquisitions/{id}/timeline`

- **Auth:** required  
- **Response 200:** `{ "data": { "stages": [...catalogue...], "events": [ { "from_stage", "to_stage", "occurred_at", "actor", "remarks", "document_id" } ] } }`

### `POST /api/acquisitions/{id}/transition`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER` for most; `APPROVING_AUTHORITY` when `to_stage=APPROVAL`; `ADMIN` override  
- **Request:** `{ "to_stage": "SIA", "remarks": "", "document_id": null }`  
- **Response 200:** updated case + new event  
- **Errors:** 400 `ILLEGAL_TRANSITION`  
- **Audit:** `WORKFLOW_STAGE_CHANGED`  
- **Side effect:** `alert_service.evaluate_case(id)`

---

## 8. Documents — `/api/documents`

### `GET /api/documents`

- **Auth:** required · **Query:** `project_id`, `parcel_id`, `proposal_id`, `doc_type`  
- **Role:** any (scoped)

### `POST /api/documents`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`, `FIELD_OFFICER`, `ADMIN`  
- **Content-Type:** `multipart/form-data`  
- **Fields:** `file`, `name`, `doc_type`, `project_id?`, `parcel_id?`, `proposal_id?`, `acquisition_case_id?`  
- **Response 201:** metadata (`verification_status=PENDING`)  
- **Audit:** `DOCUMENT_UPLOADED`  
- **Errors:** 400 missing file; 413 if >10 MB (prototype cap)

### `GET /api/documents/{id}`

- metadata only

### `GET /api/documents/{id}/file`

- **Auth:** required · **Role:** any with access  
- **Response:** binary stream (`Content-Type` original)

### `POST /api/documents/{id}/verify`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`, `APPROVING_AUTHORITY`  
- **Request:** `{ "verification_status": "VERIFIED"|"REJECTED", "remarks": "" }`  
- **Audit:** `DOCUMENT_VERIFIED`

---

## 9. Compensation — `/api/compensation`

### `GET /api/compensation`

- **Auth:** required · **Role:** `ADMIN`, `ACQUISITION_OFFICER`, `APPROVING_AUTHORITY`  
- **Query:** `project_id`, `status`

### `GET /api/compensation/{id}`

- **Auth:** required · same roles

### `POST /api/compensation`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`  
- **Request:** `{ "acquisition_case_id", "assessed_amount_inr", "due_date", "remarks" }`  
- **Response 201:** `status=ASSESSED`  
- **Errors:** 409 if case already has compensation row (use PATCH)

### `PATCH /api/compensation/{id}`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`  
- **Request:** `{ "paid_amount_inr", "payment_date", "status", "remarks" }`  
- **Audit:** `COMPENSATION_UPDATED`  
- **Side effect:** if `due_date` near, alert rule may fire

---

## 10. Rehabilitation & resettlement — `/api/rehabilitation`

### `GET /api/rehabilitation`

- **Auth:** required · **Role:** admin, officer, authority  
- **Query:** `project_id`, `status`

### `PATCH /api/rehabilitation/{id}`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`  
- **Request:** `{ "status", "amount_inr", "package_type", "completion_date" }`

### `GET /api/resettlement`  and  `PATCH /api/resettlement/{id}`

- Same auth pattern  
- **Request PATCH:** `{ "status", "site_name", "plot_allotted", "possession_date" }`

### `GET /api/rehabilitation/families`

- Combined family + rehab + resettlement view for R&R page

---

## 11. Possession — `/api/possession`

### `GET /api/possession`

- **Auth:** required · **Role:** admin, officer, authority  
- **Query:** `project_id`, `status`

### `POST /api/possession`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`  
- **Request:** `{ "acquisition_case_id", "status", "area_ha", "taken_at", "remarks" }`  
- **Response 201**  
- **Errors:** 409 duplicate for case

### `PATCH /api/possession/{id}`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`

---

## 12. Field verification — `/api/field-verification`

### `GET /api/field-verification`

- **Auth:** required  
- **Role:** `FIELD_OFFICER` → only `assigned_to = me`; others see all (filtered)  
- **Query:** `status`, `parcel_id`

### `GET /api/field-verification/{id}`

- Includes parcel summary + existing photos

### `PATCH /api/field-verification/{id}`

- **Auth:** required · **Role:** assigned `FIELD_OFFICER`  
- **Request:** `{ "gps_lat", "gps_lng", "owner_verified", "land_info_verified", "documents_verified", "remarks" }`  
- **Note:** client may send browser Geolocation coords.

### `POST /api/field-verification/{id}/photos`

- **multipart** `file` · **Role:** assigned field officer  
- Creates `documents` with `doc_type=PHOTO`

### `POST /api/field-verification/{id}/submit`

- **Auth:** required · **Role:** assigned `FIELD_OFFICER`  
- **Request:** `{ "remarks": "" }` plus persisted GPS/flags  
- **Response 200:** `status=SUBMITTED`  
- **Errors:** 400 if GPS missing  
- **Audit:** `FIELD_VERIFICATION_SUBMITTED`

---

## 13. Notifications & alerts

### `GET /api/notifications`

- **Auth:** required · **Role:** self only  
- **Query:** `unread=true`

### `PATCH /api/notifications/{id}/read`

- **Auth:** required · owner only · **Response 200**

### `POST /api/notifications/read-all`

- **Auth:** required · **Response 204**

### `GET /api/alerts`

- **Auth:** required · recipient = current user unless `ADMIN`  
- **Query:** `severity`, `unread`, `rule_code`, `project_id`

### `PATCH /api/alerts/{id}/read`

- **Auth:** required · recipient or admin

### `POST /api/alerts/evaluate`

- **Auth:** required · **Role:** `ADMIN`  
- **Request:** `{ "project_id": null }`  
- **Response 200:** `{ "data": { "created": 4 } }`  
- **Purpose:** demo “run rules now” (no cron)

---

## 14. Reports — `/api/reports`

All: **Auth** required · **Role:** `ADMIN`, `APPROVING_AUTHORITY`, `ACQUISITION_OFFICER`  
Query: shared filters  
Response: tabular arrays suitable for Recharts / CSV later.

### `GET /api/reports/acquisition-summary`

Per project: notified/acquired area, stage counts, delay flag.

### `GET /api/reports/compensation`

Assessed vs paid by project/district.

### `GET /api/reports/rr`

Families, displaced, rehab/resettlement completion %.

### `GET /api/reports/timeline`

Expected vs actual stage durations.

---

## 15. GIS — `/api/gis`

All GIS payloads set `"meta": { "data_source": "SYNTHETIC", "basemap": "OpenStreetMap", "cadastral_disclaimer": "Geometries are synthetic. Not live cadastral data." }`

### `GET /api/gis/states`

- **Auth:** required · **Role:** any  
- **Response:** GeoJSON FeatureCollection of state centroids or simplified polygons

### `GET /api/gis/districts?state_code=`

- District list with optional centroids

### `GET /api/gis/projects/{id}/geojson`

- FeatureCollection of parcels in project, properties: ulpin, status, stage, area_ha

### `GET /api/gis/parcels`

- **Query:** `bbox=minLng,minLat,maxLng,maxLat` **or** shared filters  
- **Response:** GeoJSON FeatureCollection  
- **Cap:** 500 features; 400 if unfiltered and would exceed

### `GET /api/gis/parcels/{id}/geojson`

- Single Feature

---

## 16. ML — `/api/ml`

See also [E-ml-interface.md](./E-ml-interface.md).

### `POST /api/ml/predict-delay`

- **Auth:** required · **Role:** `ADMIN`, `ACQUISITION_OFFICER`, `APPROVING_AUTHORITY`  
- **Request:** `{ "acquisition_case_id": "uuid" }`  
  Optional override: `{ "features": { ... } }` for demo without a case.  
- **Response 200:**

```json
{
  "data": {
    "acquisition_case_id": "uuid",
    "risk_level": "HIGH",
    "risk_score": 0.78,
    "model_version": "rf-delay-v1",
    "trained_on": "SYNTHETIC",
    "disclaimer": "Model trained on synthetic demonstration data, not government historical records.",
    "features_used": { }
  }
}
```

- **Errors:** 404 case; 503 if `model.pkl` missing (`MODEL_NOT_LOADED`)  
- **Side effect:** persist `ml_predictions`; if HIGH, create `ML_HIGH_RISK` alert

### `GET /api/ml/predictions`

- Latest prediction per case, filterable by `risk_level`, `project_id`

### `GET /api/ml/predictions/{case_id}`

- History for a case

---

## 17. Integrations — `/api/integrations`

Never claims live connectivity unless an adapter is actually configured and healthy.

### `GET /api/integrations/status`

- **Auth:** required · **Role:** `ADMIN`  
- **Response 200:**

```json
{
  "data": {
    "mode": "mock",
    "adapters": [
      {
        "name": "land_records",
        "availability": "UNAVAILABLE_PUBLIC",
        "implementation": "MOCK",
        "requires_authorization": true,
        "healthy": true
      },
      {
        "name": "cadastral_maps",
        "availability": "UNAVAILABLE_PUBLIC",
        "implementation": "MOCK",
        "requires_authorization": true,
        "healthy": true
      },
      {
        "name": "registration",
        "availability": "UNAVAILABLE_PUBLIC",
        "implementation": "MOCK",
        "requires_authorization": true,
        "healthy": true
      },
      {
        "name": "acquisition_data",
        "availability": "UNAVAILABLE_PUBLIC",
        "implementation": "MOCK",
        "requires_authorization": true,
        "healthy": true
      }
    ]
  }
}
```

`availability` enum: `AVAILABLE_VERIFIED` | `REQUIRES_AUTHORIZATION` | `UNAVAILABLE_PUBLIC` | `MOCK_ONLY`

### `POST /api/integrations/land-records/lookup`

- **Auth:** required · **Role:** `ACQUISITION_OFFICER`, `ADMIN`  
- **Request:** `{ "ulpin": "" }` **or** `{ "state_code", "district_code", "khasra_number" }`  
- **Response 200:** normalized parcel DTO + `"meta": { "data_source": "MOCK_ADAPTER" }`  
- **Errors:** 404 mock miss; 503 if mode=external and no credentials (`INTEGRATION_UNAVAILABLE`)

### `POST /api/integrations/cadastral/parcel`

- **Request:** `{ "ulpin": "" }`  
- **Response 200:** GeoJSON Feature + `data_source=MOCK_ADAPTER`

### `GET /api/integrations/health`

- Public or admin; liveness of mock adapters (always 200 in prototype)

---

## 18. Audit — `/api/audit-logs`

### `GET /api/audit-logs`

- **Auth:** required · **Role:** `ADMIN`  
- **Query:** `user_id`, `action`, `entity_type`, `entity_id`, `date_from`, `date_to`, `page`  
- **Response 200:** paginated logs

---

## Role × endpoint matrix (summary)

| Area | ADMIN | ACQ OFFICER | APPROVER | FIELD |
|---|---|---|---|---|
| Login / me | ✓ | ✓ | ✓ | ✓ |
| Users CRUD | ✓ | — | — | — |
| Dashboard / GIS read | ✓ | ✓ | ✓ | ✓ (assigned) |
| Projects write | ✓ | ✓ | — | — |
| Parcels write | ✓ | ✓ | — | — |
| Proposals create/submit | — | ✓ | — | — |
| Proposals approve/reject | — | — | ✓ | — |
| Workflow transition | override | ✓ | approval stage | — |
| Documents upload | ✓ | ✓ | — | photos |
| Compensation / R&R / possession write | — | ✓ | read | — |
| Field submit | — | — | — | ✓ assigned |
| Alerts evaluate | ✓ | — | — | — |
| ML predict | ✓ | ✓ | ✓ | — |
| Integrations status | ✓ | lookup | — | — |
| Audit logs | ✓ | — | — | — |
