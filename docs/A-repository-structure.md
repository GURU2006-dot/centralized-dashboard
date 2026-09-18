# A. Repository structure

Monorepo. One backend process, one Vite SPA, one PostgreSQL. No application source is created in this phase — this is the **target tree**.

```
sih-26016-land-acquisition/
├── README.md                          # run instructions + SYNTHETIC DATA disclaimer
├── docker-compose.yml                 # postgres:16-postgis + optional api/web later
├── .env.example
├── .gitignore
│
├── docs/                              # THIS architecture pack
│   ├── README.md
│   ├── 00-analysis.md
│   ├── A-repository-structure.md
│   ├── B-database-erd.md
│   ├── C-api-contracts.md
│   ├── D-frontend-component-hierarchy.md
│   ├── E-ml-interface.md
│   ├── F-integration-interfaces.md
│   ├── G-auth-rbac.md
│   ├── H-implementation-plan.md
│   ├── I-one-day-execution-plan.md
│   └── J-architecture-decisions.md
│
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/                  # 0001_initial.py (when implementation starts)
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_dashboard.py
│   │   ├── test_parcels.py
│   │   ├── test_workflow.py
│   │   └── test_ml_predict.py
│   └── app/
│       ├── main.py                    # FastAPI app, CORS, routers
│       ├── config.py                  # pydantic-settings from env
│       ├── deps.py                    # DB session, current_user, require_roles
│       ├── logging.py
│       ├── errors.py                  # unified error envelope
│       ├── security.py                # JWT, password hash
│       │
│       ├── api/                       # routers only — no business logic
│       │   ├── router.py              # mounts all /api/*
│       │   ├── auth.py
│       │   ├── users.py
│       │   ├── dashboard.py
│       │   ├── projects.py
│       │   ├── parcels.py
│       │   ├── proposals.py
│       │   ├── acquisitions.py
│       │   ├── documents.py
│       │   ├── compensation.py
│       │   ├── rehabilitation.py
│       │   ├── possession.py
│       │   ├── field_verification.py
│       │   ├── notifications.py
│       │   ├── alerts.py
│       │   ├── reports.py
│       │   ├── gis.py
│       │   ├── ml.py
│       │   ├── integrations.py
│       │   └── audit.py
│       │
│       ├── schemas/                   # Pydantic v2 request/response
│       │   ├── common.py              # ErrorResponse, Page, DataSource
│       │   ├── auth.py
│       │   ├── dashboard.py
│       │   ├── project.py
│       │   ├── parcel.py
│       │   ├── proposal.py
│       │   ├── acquisition.py
│       │   ├── document.py
│       │   ├── compensation.py
│       │   ├── rr.py
│       │   ├── field_verification.py
│       │   ├── alert.py
│       │   ├── gis.py
│       │   ├── ml.py
│       │   └── integration.py
│       │
│       ├── models/                    # SQLAlchemy 2.0
│       │   ├── base.py
│       │   ├── enums.py
│       │   ├── user.py
│       │   ├── geo.py                 # State, District
│       │   ├── project.py
│       │   ├── parcel.py
│       │   ├── owner.py
│       │   ├── acquisition.py
│       │   ├── proposal.py
│       │   ├── document.py
│       │   ├── compensation.py
│       │   ├── family.py              # affected, rehab, resettlement
│       │   ├── possession.py
│       │   ├── field_verification.py
│       │   ├── notification.py
│       │   ├── alert.py
│       │   ├── ml_prediction.py
│       │   └── audit.py
│       │
│       ├── repositories/              # SQL only
│       │   ├── user_repo.py
│       │   ├── project_repo.py
│       │   ├── parcel_repo.py
│       │   ├── proposal_repo.py
│       │   ├── acquisition_repo.py
│       │   ├── dashboard_repo.py
│       │   └── ...
│       │
│       ├── services/                  # business rules, transactions, audit calls
│       │   ├── auth_service.py
│       │   ├── dashboard_service.py
│       │   ├── project_service.py
│       │   ├── parcel_service.py
│       │   ├── proposal_service.py
│       │   ├── workflow_service.py    # stage machine
│       │   ├── document_service.py
│       │   ├── compensation_service.py
│       │   ├── field_verification_service.py
│       │   ├── alert_service.py       # rule evaluation
│       │   ├── report_service.py
│       │   ├── gis_service.py
│       │   ├── audit_service.py
│       │   └── ml_service.py          # thin wrapper over app.ml.predict
│       │
│       ├── workflow/
│       │   ├── stages.py              # catalogue + allowed transitions
│       │   └── engine.py              # apply_transition()
│       │
│       ├── ml/                        # isolated from business logic
│       │   ├── preprocessing.py
│       │   ├── train.py
│       │   ├── predict.py
│       │   ├── evaluation.py
│       │   ├── features.py            # feature name contract
│       │   └── artifacts/
│       │       ├── model.pkl          # generated, not hand-authored
│       │       └── metrics.json
│       │
│       └── integrations/              # adapter layer (R11)
│           ├── base.py                # Protocol + Normalized* DTOs
│           ├── land_records.py
│           ├── cadastral.py
│           ├── registration.py
│           ├── acquisition_data.py
│           ├── mock/
│           │   ├── land_records.py
│           │   ├── cadastral.py
│           │   ├── registration.py
│           │   └── acquisition_data.py
│           └── factory.py             # env INTEGRATION_MODE=mock|external
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── public/
│   │   └── disclaimer.txt
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── config.js                  # VITE_API_BASE, DISCLAIMER
│       ├── auth/
│       │   ├── AuthContext.jsx
│       │   ├── ProtectedRoute.jsx
│       │   └── roles.js
│       ├── api/                       # fetch wrappers, one file per resource
│       │   ├── client.js              # base fetch + JWT + error unwrap
│       │   ├── auth.js
│       │   ├── dashboard.js
│       │   ├── projects.js
│       │   ├── parcels.js
│       │   ├── proposals.js
│       │   ├── acquisitions.js
│       │   ├── documents.js
│       │   ├── compensation.js
│       │   ├── gis.js
│       │   ├── alerts.js
│       │   ├── fieldVerification.js
│       │   ├── reports.js
│       │   └── ml.js
│       ├── layouts/
│       │   ├── AppLayout.jsx          # sidebar + header + outlet
│       │   ├── Sidebar.jsx
│       │   ├── Header.jsx
│       │   └── AuthLayout.jsx
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   ├── DashboardPage.jsx
│       │   ├── ProjectsPage.jsx
│       │   ├── ProjectDetailPage.jsx
│       │   ├── ParcelsPage.jsx
│       │   ├── ParcelDetailPage.jsx
│       │   ├── ProposalsPage.jsx
│       │   ├── ProposalFormPage.jsx
│       │   ├── ProposalReviewPage.jsx
│       │   ├── AcquisitionWorkflowPage.jsx
│       │   ├── GisMapPage.jsx
│       │   ├── CompensationPage.jsx
│       │   ├── RRPage.jsx
│       │   ├── FieldVerificationPage.jsx
│       │   ├── FieldVerificationSubmitPage.jsx
│       │   ├── AlertsPage.jsx
│       │   ├── ReportsPage.jsx
│       │   ├── MlInsightsPage.jsx
│       │   └── AdminPage.jsx
│       ├── components/
│       │   ├── ui/
│       │   │   ├── Button.jsx
│       │   │   ├── Card.jsx
│       │   │   ├── Badge.jsx          # status / stage / data_source
│       │   │   ├── Modal.jsx
│       │   │   ├── Table.jsx
│       │   │   ├── Pagination.jsx
│       │   │   ├── EmptyState.jsx
│       │   │   ├── Spinner.jsx
│       │   │   └── DisclaimerBanner.jsx
│       │   ├── forms/
│       │   │   ├── TextField.jsx
│       │   │   ├── SelectField.jsx
│       │   │   ├── DateField.jsx
│       │   │   ├── FileUpload.jsx
│       │   │   └── FilterBar.jsx
│       │   ├── dashboard/
│       │   │   ├── KpiCard.jsx
│       │   │   ├── KpiGrid.jsx
│       │   │   └── ChartPanel.jsx
│       │   ├── workflow/
│       │   │   ├── StageTimeline.jsx
│       │   │   └── TransitionModal.jsx
│       │   ├── map/
│       │   │   ├── ParcelMap.jsx
│       │   │   ├── ParcelPopup.jsx
│       │   │   └── LayerLegend.jsx
│       │   └── alerts/
│       │       └── AlertList.jsx
│       └── utils/
│           ├── format.js              # INR, ha, dates
│           └── constants.js           # stages, statuses
│
├── data/
│   ├── README.md                      # “ALL FILES ARE SYNTHETIC”
│   ├── seed/
│   │   ├── states.csv
│   │   ├── districts.csv
│   │   ├── users.csv
│   │   ├── projects.csv
│   │   ├── parcels.csv
│   │   ├── owners.csv
│   │   ├── parcel_owners.csv
│   │   ├── proposals.csv
│   │   ├── acquisition_cases.csv
│   │   ├── workflow_events.csv
│   │   ├── compensation.csv
│   │   ├── families.csv
│   │   ├── alerts.csv
│   │   └── documents_meta.csv
│   ├── geo/
│   │   ├── parcels.geojson            # SYNTHETIC polygons
│   │   └── states_simplified.geojson  # optional choropleth
│   ├── ml/
│   │   ├── train.csv                  # SYNTHETIC training set
│   │   └── feature_dict.json
│   └── uploads/                       # runtime; gitkeep only
│       └── .gitkeep
│
└── scripts/
    ├── seed_db.py                     # load CSVs + geojson
    ├── train_ml.py                    # calls app.ml.train
    └── demo_reset.py                  # drop+seed for judges
```

## Boundary rules

| Layer | May import | Must not import |
|---|---|---|
| `api/` | `schemas`, `services`, `deps` | `models` (except via services), `ml.train` |
| `services/` | `repositories`, `models`, `workflow`, `integrations`, `ml.predict` | FastAPI `Request` |
| `ml/` | numpy/sklearn, `ml/features.py` | FastAPI, SQLAlchemy, `services` |
| `integrations/` | `schemas` DTOs / own dataclasses | `services`, routers |
| `frontend/src/api` | `client.js` | Leaflet, page components |
| `frontend/src/pages` | components + api | raw `fetch` |

## What is deliberately absent

- `kubernetes/`, `terraform/` — not a one-day need.
- `services/notification_queue.py` — in-process alerts.
- `packages/` multi-package workspaces.
- Native `mobile/` app.
