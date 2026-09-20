# NLAMP AI Brain

## 1. Project Identity

Project: National Land Acquisition Management & Intelligence Platform (NLAMP)

SIH Problem Statement: 26016

Repository root:
C:\Users\bhanu\OneDrive\Desktop\sih

Purpose:
A prototype centralized land acquisition management and intelligence platform combining workflow management, GIS, compensation/possession tracking, role-based access control, field verification, auditability, and prototype ML-based risk analysis.

This is a prototype for demonstration.

## 2. Source-of-Truth Rule

Priority order:

1. Actual source code and database schema
2. Automated tests and API contracts
3. Architecture/freeze documentation
4. AI_BRAIN.md
5. SESSION_MEMORY.md

If memory files conflict with the implementation, trust the implementation and tests.

Never blindly apply information from this file without checking the relevant source file when modifying behavior.

## 3. Architecture

The repository is a monorepo:

backend/
- FastAPI REST API
- SQLAlchemy ORM
- PostgreSQL/PostGIS
- Alembic migrations
- JWT authentication
- RBAC
- business services
- repositories
- workflow engine
- GIS services
- ML services
- mock government integrations
- pytest tests

frontend/
- React 19
- Vite
- Tailwind CSS
- React Router
- Axios
- Leaflet / React-Leaflet
- Recharts
- Lucide
- lazy-loaded protected routes

data/
- synthetic geospatial data
- local document upload storage

docs/
- architecture specifications
- ADRs
- testing reports
- freeze rules

scripts/
- database seed/reset
- ML training
- API/E2E validation

docker-compose.yml
- PostgreSQL/PostGIS development service

## 4. Backend Layering

Use this mental model:

HTTP/API
    ↓
Services / business logic
    ↓
Repositories / data access
    ↓
SQLAlchemy models
    ↓
PostgreSQL/PostGIS

Other important layers:

- Pydantic schemas for request/response validation
- Workflow engine for acquisition-case state transitions
- Integration ports/adapters for external systems
- Centralized application errors
- Audit/event logging

Important files:

backend/app/main.py
backend/app/api/router.py
backend/app/config.py
backend/app/security.py
backend/app/deps.py
backend/app/errors.py
backend/app/models/enums.py
backend/app/workflow/engine.py
backend/app/services/proposals.py
backend/app/services/scope.py
backend/app/schemas/common.py

## 5. Frontend Architecture

Important frontend files:

frontend/src/App.jsx
frontend/src/components/layout.jsx
frontend/src/components/ui.jsx
frontend/src/components/ParcelMap.jsx
frontend/src/context/AuthContext.jsx
frontend/src/lib/roles.js
frontend/src/api/client.js

Pages are lazy-loaded and protected by authentication/RBAC.

The Axios client:
- uses the Vite proxy during development
- attaches the JWT Authorization header
- handles authentication expiry
- unwraps the standard API response envelope

Do not replace this API architecture unnecessarily.

## 6. Authentication and Roles

The system uses JWT authentication and RBAC.

Defined roles:

ADMIN
ACQUISITION_OFFICER
APPROVING_AUTHORITY
FIELD_OFFICER

Backend authorization is authoritative.

Frontend role gating is for UI/navigation behavior and must never be treated as the only security boundary.

Geographic scope is enforced on the backend.

Sensitive owner PII must not be exposed through public parcel/GIS responses.

## 7. Core Proposal Rule

Proposal approval is authoritative.

The lifecycle is:

Proposal creation
→ submission
→ verification/review
→ approval or rejection

When a proposal is approved, the system creates the acquisition case(s).

There is NO second acquisition-case approval step.

Do not introduce a duplicate approval workflow.

Relevant files:

frontend/src/pages/ProposalFormPage.jsx
frontend/src/pages/ProposalsPage.jsx
frontend/src/pages/ProposalDetailPage.jsx
frontend/src/api/proposals.js

backend/app/api/proposals.py
backend/app/services/proposals.py
backend/app/models/proposal.py

## 8. Acquisition Workflow

The authoritative acquisition workflow is:

SIA
→ NOTIFICATION
→ AWARD
→ COMPENSATION_ASSESSMENT
→ COMPENSATION_PAID
→ POSSESSION
→ REHABILITATION_RESETTLEMENT
→ COMPLETED

The workflow engine enforces valid transitions and stage gates.

Never allow arbitrary stage skipping.

Relevant files:

backend/app/workflow/engine.py
backend/app/workflow/stages.py
backend/app/api/acquisitions.py
backend/app/models/acquisition.py
backend/app/schemas/workflow.py

Frontend:

frontend/src/pages/WorkflowPage.jsx
frontend/src/pages/AcquisitionsPage.jsx
frontend/src/pages/AcquisitionDetailPage.jsx
frontend/src/api/acquisitions.js

## 9. GIS

GIS uses:

- PostgreSQL/PostGIS
- GeoAlchemy2
- Leaflet
- React-Leaflet
- GeoJSON

Important files:

frontend/src/pages/GisMapPage.jsx
frontend/src/components/ParcelMap.jsx
frontend/src/api/gis.js

backend/app/api/gis.py
backend/app/services/gis.py
backend/app/models/parcel.py
backend/app/services/scope.py

GIS must preserve:
- geographic filtering
- role-based geographic scope
- parcel geometry handling
- error/empty states
- accessible fallback/table behavior where already implemented

Do not expose owner PII through GIS endpoints.

## 10. Compensation / Possession / R&R

Case-linked operational modules include:

- Compensation
- Possession
- Rehabilitation
- Resettlement

Relevant frontend grouping:

frontend/src/pages/CaseLinkedPage.jsx

Backend APIs/services are separated by domain.

Respect workflow gates when changing these modules.

## 11. Field Verification

Field operations are represented by:

frontend/src/pages/FieldPages.jsx

backend/app/api/field_verification.py
backend/app/services/field_verification.py
backend/app/models/field_verification.py

Field verification includes location/GPS-related requirements.

Do not weaken validation requirements merely to make UI tests pass.

## 12. ML / Risk

The project contains a scikit-learn Random Forest prototype for acquisition delay-risk analysis.

Important files:

backend/app/ml/features.py
backend/app/ml/predictor.py
backend/app/ml/train.py
backend/app/services/ml.py
backend/app/services/ml_features.py
backend/app/api/ml.py

The displayed value is a prototype risk index.

IMPORTANT:
Do not describe the risk score as a calibrated probability of delay.

Use terminology such as:

"Prototype Risk Index"

unless the actual implementation/documentation is changed and validated.

ML results are based on synthetic prototype data.

## 13. Government Integrations

Government integrations remain MOCK ONLY.

Integration architecture uses ports/adapters.

Relevant files:

backend/app/integrations/base.py
backend/app/integrations/mock.py
backend/app/integrations/factory.py
backend/app/services/integrations.py

Do not claim that Bhoomi, Bhunaksha, Kaveri, Khajane, or other government systems are live integrations.

Do not replace mock integrations with real government APIs without an explicit project decision.

## 14. Synthetic Data

The prototype must retain this disclaimer:

"All projects, parcels, owners, geometries, compensation figures, and ML scores in this prototype are synthetic demonstration data. They are not live land records, cadastral maps, or government statistics."

Do not remove or weaken this disclaimer.

## 15. API Contract

The backend uses a standard response envelope containing:

data
meta

Errors use the application's centralized error format.

Before changing an API response:
- inspect existing frontend consumers
- inspect backend schemas
- inspect relevant tests
- preserve compatibility where possible

Do not casually rename fields or change response shapes.

## 16. Database

Database architecture:

PostgreSQL + PostGIS

SQLAlchemy 2.x
GeoAlchemy2
Alembic

Database configuration is environment-dependent.

IMPORTANT:
Do not hardcode a PostgreSQL host port based on documentation or memory.

Use the current `.env`, `.env.example`, docker-compose configuration, and runtime environment as the source of truth.

Do not change database configuration merely to make a test or command work.

## 17. Performance / Frontend Loading

Protected application routes use lazy loading/code splitting.

Important principle:

Do not remove lazy loading or introduce a large global bundle without evidence that it is necessary.

Avoid unnecessary imports of heavy GIS/charting libraries into unrelated routes.

## 18. Testing

Backend:

cd backend
pytest -q

Frontend build:

cd frontend
npm run build

Frontend lint:

cd frontend
npm run lint

API validation:

python scripts/phase5_validate.py

Database reset:

python scripts/demo_reset.py

Seed:

python scripts/seed_db.py

Do not hardcode an exact test-count number in this memory file. The suite can change.

## 19. Task-to-File Routing

For dashboard work:

frontend/src/pages/DashboardPage.jsx
frontend/src/api/dashboard.js
frontend/src/components/ui.jsx

backend/app/api/dashboard.py
backend/app/services/dashboard.py
backend/app/repositories/dashboard.py
backend/app/schemas/dashboard.py

For navigation:

frontend/src/components/layout.jsx
frontend/src/lib/roles.js
frontend/src/App.jsx

For proposals:

frontend/src/pages/ProposalFormPage.jsx
frontend/src/pages/ProposalsPage.jsx
frontend/src/pages/ProposalDetailPage.jsx
frontend/src/api/proposals.js

backend/app/api/proposals.py
backend/app/services/proposals.py

For GIS:

frontend/src/pages/GisMapPage.jsx
frontend/src/components/ParcelMap.jsx
frontend/src/api/gis.js

backend/app/api/gis.py
backend/app/services/gis.py
backend/app/services/scope.py

For workflow:

frontend/src/pages/WorkflowPage.jsx
frontend/src/pages/AcquisitionsPage.jsx
frontend/src/pages/AcquisitionDetailPage.jsx

backend/app/workflow/engine.py
backend/app/workflow/stages.py
backend/app/api/acquisitions.py

For authentication/RBAC:

frontend/src/pages/LoginPage.jsx
frontend/src/context/AuthContext.jsx
frontend/src/lib/roles.js
frontend/src/api/client.js

backend/app/api/auth.py
backend/app/security.py
backend/app/deps.py

For ML:

frontend/src/pages/AcquisitionDetailPage.jsx
frontend/src/pages/AlertsNotificationsAudit.jsx
frontend/src/api/ml.js

backend/app/api/ml.py
backend/app/services/ml.py
backend/app/ml/features.py
backend/app/ml/predictor.py

For field verification:

frontend/src/pages/FieldPages.jsx
frontend/src/api/fieldVerification.js

backend/app/api/field_verification.py
backend/app/services/field_verification.py

## 20. Agent Context Efficiency

When starting a task:

1. Read AI_BRAIN.md.
2. Read AI_RULES.md.
3. Read SESSION_MEMORY.md if it contains relevant current-task information.
4. Identify the smallest set of relevant source files.
5. Inspect those files.
6. Make the smallest correct change.
7. Run targeted tests first.
8. Run broader validation when appropriate.

Do NOT:
- recursively read the entire repository for a small task
- inspect unrelated modules
- duplicate documentation that already exists
- rewrite working architecture without evidence
- modify unrelated files

If more context is genuinely required, expand inspection gradually.

## 21. Documentation Hierarchy

Useful architectural documentation includes:

docs/architecture-freeze.md
docs/FINAL-ARCHITECTURE.md
docs/FINAL-TEST-REPORT.md

Read these when the task concerns architecture, workflow rules, testing status, or project-wide constraints.

Do not read every document by default.