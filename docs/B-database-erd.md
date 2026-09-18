# B. Database ERD

**Engine:** PostgreSQL 16  
**Extensions:** `postgis` (preferred), `pgcrypto` (gen_random_uuid)  
**Fallback:** if PostGIS is unavailable, `land_parcels.geom` is omitted and `geometry_geojson JSONB` is used. API contracts stay GeoJSON either way.

All operational tables include `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` and `updated_at` where mutable.  
Prototype rows set `data_source = 'SYNTHETIC'` unless produced by a mock adapter (`MOCK_ADAPTER`).

---

## 1. Entity catalogue

### 1.1 Identity & RBAC

**roles**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| code | VARCHAR(32) | UNIQUE NOT NULL — `ADMIN`, `ACQUISITION_OFFICER`, `APPROVING_AUTHORITY`, `FIELD_OFFICER` |
| name | VARCHAR(64) | NOT NULL |
| description | TEXT | |

**users**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(128) | NOT NULL |
| role_id | UUID | FK roles.id NOT NULL |
| state_code | CHAR(2) | FK states.code NULL — geographic scope |
| district_code | VARCHAR(8) | FK districts.code NULL |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| last_login_at | TIMESTAMPTZ | |

### 1.2 Geography lookups

**states** — `code PK CHAR(2)`, `name`, `centroid_lat`, `centroid_lng`  
**districts** — `code PK`, `state_code FK`, `name`

### 1.3 Projects & land

**projects**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| code | VARCHAR(32) | UNIQUE NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| purpose | TEXT | NOT NULL |
| requiring_body | VARCHAR(255) | |
| state_code | CHAR(2) | FK NOT NULL |
| district_code | VARCHAR(8) | FK |
| estimated_area_ha | NUMERIC(14,4) | CHECK >= 0 |
| estimated_compensation_inr | NUMERIC(18,2) | CHECK >= 0 |
| start_date | DATE | |
| expected_end_date | DATE | |
| status | VARCHAR(24) | `PLANNED\|ACTIVE\|DELAYED\|ON_HOLD\|COMPLETED` |
| current_stage | VARCHAR(40) | FK workflow_stage_definitions.code |
| created_by | UUID | FK users.id |
| data_source | VARCHAR(20) | NOT NULL DEFAULT `SYNTHETIC` |

**land_parcels**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| ulpin | VARCHAR(14) | UNIQUE NOT NULL |
| khasra_number | VARCHAR(64) | NOT NULL |
| village | VARCHAR(128) | |
| tehsil | VARCHAR(128) | |
| state_code | CHAR(2) | FK NOT NULL |
| district_code | VARCHAR(8) | FK NOT NULL |
| area_ha | NUMERIC(14,4) | NOT NULL CHECK > 0 |
| project_id | UUID | FK projects.id NULL |
| acquisition_status | VARCHAR(24) | `NOT_STARTED\|IN_PROCESS\|ACQUIRED\|DISPUTED\|DROPPED` |
| current_stage | VARCHAR(40) | |
| centroid | geography(Point,4326) | NULL |
| geom | geometry(MultiPolygon,4326) | NULL |
| geometry_geojson | JSONB | NULL — fallback / cache |
| data_source | VARCHAR(20) | NOT NULL DEFAULT `SYNTHETIC` |

**owners**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| father_or_spouse_name | VARCHAR(255) | |
| id_type | VARCHAR(24) | |
| id_number | VARCHAR(64) | |
| phone | VARCHAR(20) | |
| address | TEXT | |
| data_source | VARCHAR(20) | NOT NULL DEFAULT `SYNTHETIC` |

**parcel_owners** (M:N)

| Column | Type | Constraints |
|---|---|---|
| parcel_id | UUID | PK, FK land_parcels.id ON DELETE CASCADE |
| owner_id | UUID | PK, FK owners.id |
| ownership_share_pct | NUMERIC(5,2) | CHECK 0–100 |
| ownership_type | VARCHAR(24) | `SOLE\|JOINT\|LEGAL_HEIR\|ENCUMBERED` |

### 1.4 Proposals & workflow

**workflow_stage_definitions** (catalogue — extend by INSERT)

| Column | Type | Constraints |
|---|---|---|
| code | VARCHAR(40) | PK |
| name | VARCHAR(80) | NOT NULL |
| sequence_order | INT | UNIQUE NOT NULL |
| expected_duration_days | INT | NOT NULL DEFAULT 14 |
| is_terminal | BOOLEAN | NOT NULL DEFAULT false |

**proposals**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| proposal_number | VARCHAR(32) | UNIQUE NOT NULL |
| project_id | UUID | FK projects.id NOT NULL |
| required_area_ha | NUMERIC(14,4) | NOT NULL |
| purpose | TEXT | NOT NULL |
| estimated_compensation_inr | NUMERIC(18,2) | |
| affected_families_count | INT | CHECK >= 0 |
| proposed_start | DATE | |
| proposed_end | DATE | |
| status | VARCHAR(24) | `DRAFT\|SUBMITTED\|UNDER_VERIFICATION\|APPROVED\|REJECTED` |
| submitted_by | UUID | FK users.id |
| submitted_at | TIMESTAMPTZ | |
| reviewed_by | UUID | FK users.id |
| reviewed_at | TIMESTAMPTZ | |
| review_remarks | TEXT | |

**proposal_parcels** — PK (`proposal_id`, `parcel_id`), both FKs.

**acquisition_cases** — one per (project, parcel)

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| case_number | VARCHAR(32) | UNIQUE NOT NULL |
| project_id | UUID | FK NOT NULL |
| parcel_id | UUID | FK NOT NULL |
| proposal_id | UUID | FK NULL |
| current_stage | VARCHAR(40) | FK workflow_stage_definitions.code NOT NULL |
| status | VARCHAR(24) | `OPEN\|ON_HOLD\|CLOSED\|DROPPED` |
| notified_area_ha | NUMERIC(14,4) | |
| acquired_area_ha | NUMERIC(14,4) | |
| stage_entered_at | TIMESTAMPTZ | |
| expected_stage_exit_at | TIMESTAMPTZ | |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |
| UNIQUE(project_id, parcel_id) | | |

**workflow_events** (append-only audit of transitions)

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| acquisition_case_id | UUID | FK NOT NULL |
| from_stage | VARCHAR(40) | |
| to_stage | VARCHAR(40) | NOT NULL |
| occurred_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| actor_user_id | UUID | FK users.id |
| remarks | TEXT | |
| document_id | UUID | FK documents.id NULL |
| metadata | JSONB | NOT NULL DEFAULT `{}` |

### 1.5 Documents, money, families, field

**documents**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| public_id | VARCHAR(32) | UNIQUE NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| doc_type | VARCHAR(32) | `LAND_RECORD\|SIA_REPORT\|OWNERSHIP_PROOF\|COMPENSATION\|AWARD\|RR\|PHOTO\|OTHER` |
| project_id | UUID | FK NULL |
| parcel_id | UUID | FK NULL |
| proposal_id | UUID | FK NULL |
| acquisition_case_id | UUID | FK NULL |
| storage_path | VARCHAR(512) | NOT NULL |
| mime_type | VARCHAR(128) | |
| byte_size | INT | |
| uploaded_by | UUID | FK users.id NOT NULL |
| uploaded_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| verification_status | VARCHAR(16) | `PENDING\|VERIFIED\|REJECTED` |
| verified_by | UUID | FK NULL |
| verified_at | TIMESTAMPTZ | |
| remarks | TEXT | |

**compensation** (0..1 per case)

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| acquisition_case_id | UUID | UNIQUE FK NOT NULL |
| assessed_amount_inr | NUMERIC(18,2) | |
| paid_amount_inr | NUMERIC(18,2) | NOT NULL DEFAULT 0 |
| status | VARCHAR(20) | `NOT_ASSESSED\|ASSESSED\|PARTIAL\|PAID\|DISPUTED` |
| assessment_date | DATE | |
| due_date | DATE | |
| payment_date | DATE | |
| remarks | TEXT | |

**affected_families**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | FK NOT NULL |
| parcel_id | UUID | FK NULL |
| family_head_name | VARCHAR(255) | NOT NULL |
| member_count | INT | NOT NULL CHECK > 0 |
| is_displaced | BOOLEAN | NOT NULL DEFAULT false |
| contact | VARCHAR(32) | |
| status | VARCHAR(24) | `IDENTIFIED\|ASSISTED\|RESETTLED\|CLOSED` |

**rehabilitation** — `id PK`, `family_id UNIQUE FK`, `project_id FK`, `package_type`, `amount_inr`, `status` (`NOT_STARTED\|IN_PROGRESS\|COMPLETED`), dates.

**resettlement** — `id PK`, `family_id UNIQUE FK`, `project_id FK`, `site_name`, `plot_allotted`, `status` (`NOT_ALLOTTED\|ALLOTTED\|POSSESSED`), dates.

**possession** — `id PK`, `acquisition_case_id UNIQUE FK`, `status` (`NOT_TAKEN\|PARTIAL\|TAKEN`), `area_ha`, `taken_at`, `taken_by FK users`, `remarks`.

**field_verifications**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| parcel_id | UUID | FK NOT NULL |
| acquisition_case_id | UUID | FK NULL |
| assigned_to | UUID | FK users.id NOT NULL |
| status | VARCHAR(20) | `ASSIGNED\|IN_PROGRESS\|SUBMITTED\|ACCEPTED\|REJECTED` |
| gps_lat | NUMERIC(9,6) | |
| gps_lng | NUMERIC(9,6) | |
| captured_at | TIMESTAMPTZ | |
| owner_verified | BOOLEAN | |
| land_info_verified | BOOLEAN | |
| documents_verified | BOOLEAN | |
| remarks | TEXT | |
| submitted_at | TIMESTAMPTZ | |
| submitted_by | UUID | FK |

### 1.6 Alerts, ML, audit

**notifications** — `id`, `user_id FK`, `title`, `body`, `channel` (`IN_APP`), `related_type`, `related_id`, `is_read`, `created_at`.

**alerts**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| rule_code | VARCHAR(40) | NOT NULL — `APPROVAL_PENDING`, `COMPENSATION_DUE`, `STAGE_OVERRUN`, `ML_HIGH_RISK`, `FIELD_INCOMPLETE` |
| alert_type | VARCHAR(40) | NOT NULL |
| severity | VARCHAR(16) | `LOW\|MEDIUM\|HIGH\|CRITICAL` |
| project_id | UUID | FK NULL |
| parcel_id | UUID | FK NULL |
| acquisition_case_id | UUID | FK NULL |
| message | TEXT | NOT NULL |
| recipient_user_id | UUID | FK NOT NULL |
| is_read | BOOLEAN | NOT NULL DEFAULT false |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| metadata | JSONB | NOT NULL DEFAULT `{}` |

**ml_predictions**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| acquisition_case_id | UUID | FK NOT NULL |
| project_id | UUID | FK |
| risk_level | VARCHAR(8) | `LOW\|MEDIUM\|HIGH` |
| risk_score | NUMERIC(5,4) | CHECK 0–1 |
| features | JSONB | NOT NULL |
| model_version | VARCHAR(32) | NOT NULL |
| trained_on | VARCHAR(16) | NOT NULL DEFAULT `SYNTHETIC` |
| predicted_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| predicted_by | UUID | FK NULL |

**audit_logs** (append-only)

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | UUID | FK NULL |
| action | VARCHAR(64) | NOT NULL |
| entity_type | VARCHAR(40) | NOT NULL |
| entity_id | VARCHAR(64) | NOT NULL |
| occurred_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| ip | INET | |
| metadata | JSONB | NOT NULL DEFAULT `{}` |

**dashboard_presets** (P2) — `id`, `user_id`, `name`, `filters JSONB`. Optional; skip table on day one if time-constrained.

---

## 2. Cardinality

| From | To | Rel | Notes |
|---|---|---|---|
| roles | users | 1:N | one role per user |
| states | districts | 1:N | |
| states | projects, parcels | 1:N | |
| projects | land_parcels | 1:N | parcel may be unassigned |
| land_parcels | owners | N:M | via parcel_owners |
| projects | proposals | 1:N | |
| proposals | land_parcels | N:M | via proposal_parcels |
| projects | acquisition_cases | 1:N | |
| land_parcels | acquisition_cases | 1:N | unique per project |
| proposals | acquisition_cases | 1:N | |
| acquisition_cases | workflow_events | 1:N | append-only |
| acquisition_cases | compensation | 1:0..1 | |
| acquisition_cases | possession | 1:0..1 | |
| acquisition_cases | ml_predictions | 1:N | history of scores |
| projects | affected_families | 1:N | |
| affected_families | rehabilitation | 1:0..1 | |
| affected_families | resettlement | 1:0..1 | |
| land_parcels | field_verifications | 1:N | |
| users | documents, alerts, notifications, audit | 1:N | |
| projects / parcels / cases | documents | 1:N | polymorphic FKs nullable |

---

## 3. Indexes

```
users (role_id), (email)
land_parcels (khasra_number), (state_code, district_code), (project_id), (acquisition_status)
land_parcels USING GIST (geom)            -- if PostGIS
land_parcels USING GIST (centroid)
projects (state_code, district_code), (status)
proposals (project_id, status), (submitted_by)
acquisition_cases (project_id, current_stage, status), (parcel_id)
workflow_events (acquisition_case_id, occurred_at)
documents (project_id), (parcel_id), (doc_type)
alerts (recipient_user_id, is_read, created_at DESC)
notifications (user_id, is_read)
audit_logs (entity_type, entity_id), (user_id, occurred_at DESC), (occurred_at DESC)
ml_predictions (acquisition_case_id, predicted_at DESC)
field_verifications (assigned_to, status)
affected_families (project_id), (is_displaced)
```

---

## 4. Important CHECKs / enums

- Amounts and areas `>= 0`.
- `compensation.paid_amount_inr <= assessed` is **not** enforced (partial overshoot / interest possible); UI warns.
- `data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')`.
- `trained_on IN ('SYNTHETIC','AUTHORIZED_HISTORICAL')` — prototype always `SYNTHETIC`.
- Workflow engine (not DB) enforces allowed `from_stage → to_stage`.

---

## 5. Mermaid ER diagram

```mermaid
erDiagram
    ROLE ||--o{ USER : assigns
    STATE ||--o{ DISTRICT : contains
    STATE ||--o{ PROJECT : locates
    STATE ||--o{ LAND_PARCEL : locates
    DISTRICT ||--o{ PROJECT : locates
    DISTRICT ||--o{ LAND_PARCEL : locates
    USER ||--o{ PROJECT : creates
    USER ||--o{ PROPOSAL : submits
    USER ||--o{ DOCUMENT : uploads
    USER ||--o{ ALERT : receives
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ FIELD_VERIFICATION : assigned
    USER ||--o{ AUDIT_LOG : performs

    PROJECT ||--o{ LAND_PARCEL : includes
    PROJECT ||--o{ PROPOSAL : has
    PROJECT ||--o{ ACQUISITION_CASE : has
    PROJECT ||--o{ AFFECTED_FAMILY : affects

    LAND_PARCEL ||--o{ PARCEL_OWNER : titled
    OWNER ||--o{ PARCEL_OWNER : holds
    LAND_PARCEL ||--o{ ACQUISITION_CASE : under
    LAND_PARCEL ||--o{ FIELD_VERIFICATION : verified
    LAND_PARCEL ||--o{ DOCUMENT : attached

    PROPOSAL ||--o{ PROPOSAL_PARCEL : lists
    LAND_PARCEL ||--o{ PROPOSAL_PARCEL : listed_in
    PROPOSAL ||--o{ ACQUISITION_CASE : opens
    PROPOSAL ||--o{ DOCUMENT : attached

    WORKFLOW_STAGE_DEFINITION ||--o{ ACQUISITION_CASE : current
    ACQUISITION_CASE ||--o{ WORKFLOW_EVENT : history
    ACQUISITION_CASE ||--o| COMPENSATION : valued
    ACQUISITION_CASE ||--o| POSSESSION : taken
    ACQUISITION_CASE ||--o{ ML_PREDICTION : scored
    ACQUISITION_CASE ||--o{ DOCUMENT : attached
    ACQUISITION_CASE ||--o{ ALERT : raises

    AFFECTED_FAMILY ||--o| REHABILITATION : package
    AFFECTED_FAMILY ||--o| RESETTLEMENT : site

    ROLE {
        uuid id PK
        string code UK
        string name
    }
    USER {
        uuid id PK
        string email UK
        uuid role_id FK
        string state_code
        boolean is_active
    }
    STATE {
        string code PK
        string name
    }
    DISTRICT {
        string code PK
        string state_code FK
        string name
    }
    PROJECT {
        uuid id PK
        string code UK
        string name
        string state_code FK
        string status
        string current_stage
        numeric estimated_area_ha
        string data_source
    }
    LAND_PARCEL {
        uuid id PK
        string ulpin UK
        string khasra_number
        string state_code FK
        numeric area_ha
        uuid project_id FK
        string acquisition_status
        geometry geom
        string data_source
    }
    OWNER {
        uuid id PK
        string name
        string data_source
    }
    PARCEL_OWNER {
        uuid parcel_id PK_FK
        uuid owner_id PK_FK
        numeric ownership_share_pct
    }
    PROPOSAL {
        uuid id PK
        string proposal_number UK
        uuid project_id FK
        string status
        numeric required_area_ha
        int affected_families_count
    }
    PROPOSAL_PARCEL {
        uuid proposal_id PK_FK
        uuid parcel_id PK_FK
    }
    WORKFLOW_STAGE_DEFINITION {
        string code PK
        int sequence_order
        int expected_duration_days
        boolean is_terminal
    }
    ACQUISITION_CASE {
        uuid id PK
        string case_number UK
        uuid project_id FK
        uuid parcel_id FK
        uuid proposal_id FK
        string current_stage FK
        string status
        numeric notified_area_ha
        numeric acquired_area_ha
    }
    WORKFLOW_EVENT {
        uuid id PK
        uuid acquisition_case_id FK
        string from_stage
        string to_stage
        timestamptz occurred_at
        uuid actor_user_id FK
        string remarks
    }
    DOCUMENT {
        uuid id PK
        string public_id UK
        string doc_type
        string verification_status
        uuid uploaded_by FK
    }
    COMPENSATION {
        uuid id PK
        uuid acquisition_case_id UK_FK
        numeric assessed_amount_inr
        numeric paid_amount_inr
        string status
        date due_date
    }
    AFFECTED_FAMILY {
        uuid id PK
        uuid project_id FK
        uuid parcel_id FK
        boolean is_displaced
        int member_count
    }
    REHABILITATION {
        uuid id PK
        uuid family_id UK_FK
        string status
        numeric amount_inr
    }
    RESETTLEMENT {
        uuid id PK
        uuid family_id UK_FK
        string status
        string site_name
    }
    POSSESSION {
        uuid id PK
        uuid acquisition_case_id UK_FK
        string status
        numeric area_ha
    }
    FIELD_VERIFICATION {
        uuid id PK
        uuid parcel_id FK
        uuid assigned_to FK
        string status
        numeric gps_lat
        numeric gps_lng
    }
    NOTIFICATION {
        uuid id PK
        uuid user_id FK
        boolean is_read
        string title
    }
    ALERT {
        uuid id PK
        string rule_code
        string severity
        uuid recipient_user_id FK
        boolean is_read
        uuid acquisition_case_id FK
    }
    ML_PREDICTION {
        uuid id PK
        uuid acquisition_case_id FK
        string risk_level
        numeric risk_score
        string trained_on
        string model_version
    }
    AUDIT_LOG {
        bigint id PK
        uuid user_id FK
        string action
        string entity_type
        string entity_id
        timestamptz occurred_at
    }
```

---

## 6. KPI derivation (dashboard, not extra tables)

| KPI | Source |
|---|---|
| Total projects | `COUNT(projects)` |
| Area notified | `SUM(acquisition_cases.notified_area_ha)` |
| Area acquired | `SUM(acquisition_cases.acquired_area_ha)` |
| Compensation assessed | `SUM(compensation.assessed_amount_inr)` |
| Compensation paid | `SUM(compensation.paid_amount_inr)` |
| Affected families | `COUNT(affected_families)` |
| Displaced families | `COUNT(affected_families WHERE is_displaced)` |
| Possession status | distribution of `possession.status` |
| R&R status | distribution of rehab + resettlement status |
| Delayed projects | `projects.status = 'DELAYED'` OR case `now() > expected_stage_exit_at` |
| Timeline adherence | % cases whose current stage elapsed ≤ `expected_duration_days` |

Filters: `state_code`, `district_code`, `project_id`, `current_stage`, `status`, `date_from/date_to` (on `started_at` / `projects.start_date`).
