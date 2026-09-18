# D. Frontend component hierarchy

**Stack:** React + Vite + Tailwind CSS + Recharts + Leaflet  
**Routing:** `react-router-dom`  
**Auth:** `AuthContext` holds JWT + user; `ProtectedRoute` checks role.

No page talks to `fetch` directly. Pages → `src/api/*.js` → `client.js`.

---

## 1. Tree

```
App
├── DisclaimerBanner                    # always visible: synthetic data
├── AuthProvider
└── BrowserRouter
    ├── /login
    │   └── AuthLayout
    │       └── LoginPage
    │           ├── TextField (email, password)
    │           ├── Button
    │           └── DemoAccountsHint    # four role emails, not real SSO
    │
    └── ProtectedRoute (any authenticated)
        └── AppLayout
            ├── Sidebar                 # items filtered by role
            ├── Header
            │   ├── UserMenu
            │   └── AlertBell           # unread count → AlertsPage
            └── <Outlet>
                │
                ├── /                   DashboardPage
                ├── /projects           ProjectsPage
                ├── /projects/:id       ProjectDetailPage
                ├── /parcels            ParcelsPage
                ├── /parcels/:id        ParcelDetailPage
                ├── /proposals          ProposalsPage
                ├── /proposals/new      ProposalFormPage
                ├── /proposals/:id      ProposalReviewPage
                ├── /acquisitions/:id   AcquisitionWorkflowPage
                ├── /map                GisMapPage
                ├── /compensation       CompensationPage
                ├── /rr                 RRPage
                ├── /field              FieldVerificationPage
                ├── /field/:id          FieldVerificationSubmitPage
                ├── /alerts             AlertsPage
                ├── /reports            ReportsPage
                ├── /ml                 MlInsightsPage
                └── /admin              AdminPage
```

---

## 2. Page → layout → components → API

### LoginPage

- Layout: `AuthLayout`
- Components: `TextField`, `Button`, `DisclaimerBanner`
- API: `POST /api/auth/login` via `api/auth.login`

### DashboardPage  (P0)

- Layout: `AppLayout`
- Components:
  - `FilterBar` (state, district, project, stage, status, date range)
  - `KpiGrid` → 10× `KpiCard`
  - `ChartPanel` × N wrapping Recharts `BarChart` / `PieChart` / `LineChart`
    - State-wise acquisition
    - District-wise acquisition
    - Project progress
    - Stage distribution
    - Compensation status
    - R&R status
    - Timeline adherence
- API: `dashboard.getKpis(filters)`, `dashboard.getCharts(filters)`, `dashboard.getFilters()`

### ProjectsPage

- `FilterBar`, `Table`, `Pagination`, `Badge` (status/stage), `Button` (create, admin/officer)
- API: `projects.list`

### ProjectDetailPage

- `KpiGrid` (project slice), `Table` (parcels), `StageTimeline` (aggregate), link to map
- API: `projects.get`, `parcels.list({project_id})`

### ParcelsPage  (P0 search)

- Search row: ULPIN, khasra, owner, state, district
- `Table` of results, `Badge` data_source
- API: `parcels.search`

### ParcelDetailPage  (P0)

- Sections: identity, owners, acquisition, compensation, possession, R&R, documents
- `ParcelMap` (single geometry)
- `Table` documents, `StageTimeline` if case exists
- API: `parcels.get`, `gis.parcelGeoJson`, `documents.list`

### ProposalsPage / ProposalFormPage / ProposalReviewPage  (P1)

- Form: project select, multi parcel picker (`Table` + checkboxes), area, purpose, compensation, families, dates, `FileUpload`
- Review: `Badge` status, Approve / Reject `Modal` (authority)
- API: `proposals.*`

### AcquisitionWorkflowPage  (P0)

- `StageTimeline` (12 stages)
- `TransitionModal` (to_stage, remarks, optional document)
- Case facts + latest ML chip
- API: `acquisitions.get`, `acquisitions.timeline`, `acquisitions.transition`, `ml.predictDelay`

### GisMapPage  (P0)

- `FilterBar` (state → district → project)
- `ParcelMap` (Leaflet)
  - GeoJSON layer
  - `ParcelPopup` on click (ulpin, status, link to detail)
  - `LayerLegend` (status colours)
- API: `gis.projectGeoJson` / `gis.parcels`

### CompensationPage  (P1)

- `Table` assessed vs paid, `Badge` status, edit `Modal`
- API: `compensation.list`, `compensation.patch`

### RRPage  (P1)

- Tabs or stacked tables: families, rehabilitation, resettlement
- API: `rehabilitation.families`, patch endpoints

### FieldVerificationPage / SubmitPage  (P1, mobile-first)

- List of assigned tasks (`Card` not table on small screens)
- Submit page:
  - Parcel summary
  - `Button` “Capture GPS” → `navigator.geolocation`
  - `FileUpload` photographs (`capture="environment"`)
  - Checkboxes: owner / land / documents verified
  - Remarks + Submit
- API: `fieldVerification.get`, `patch`, `photos`, `submit`

### AlertsPage  (P1)

- `AlertList` (`Badge` severity, read/unread)
- Admin: “Evaluate rules” button
- API: `alerts.list`, `alerts.markRead`, `alerts.evaluate`

### ReportsPage  (P1)

- `FilterBar` + `ChartPanel` + `Table` for three report types
- API: `reports.*`

### MlInsightsPage  (P0)

- Disclaimer banner (synthetic training)
- `Table` of cases with risk chip
- `Button` Predict on a case
- API: `ml.predictions`, `ml.predictDelay`

### AdminPage

- Tabs: Users (`Table` + create `Modal`), Audit log `Table`, Integrations status (availability badges), optional dashboard presets (P2)
- API: `users.*`, `audit.list`, `integrations.status`

---

## 3. Shared components (do not duplicate)

| Component | Used by |
|---|---|
| `AppLayout` / `Sidebar` / `Header` | all authenticated pages |
| `DisclaimerBanner` | App root + ML + GIS + Integrations |
| `KpiCard` / `KpiGrid` | Dashboard, ProjectDetail |
| `FilterBar` | Dashboard, Parcels, Map, Reports |
| `Table` / `Pagination` | most list pages |
| `Badge` | status, stage, severity, data_source |
| `Modal` | transitions, approve/reject, create user |
| `StageTimeline` | Workflow, ParcelDetail, ProjectDetail |
| `ParcelMap` / `ParcelPopup` / `LayerLegend` | GIS, ParcelDetail, Field submit |
| `FileUpload` | proposals, documents, field photos |
| `ChartPanel` | Dashboard, Reports, ML |
| `AlertList` | Alerts, Header bell dropdown |

---

## 4. Sidebar visibility by role

| Item | ADMIN | ACQ | APPR | FIELD |
|---|---|---|---|---|
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| Projects | ✓ | ✓ | ✓ | — |
| Land parcels | ✓ | ✓ | ✓ | assigned via Field |
| Proposals | ✓ | ✓ | ✓ | — |
| GIS map | ✓ | ✓ | ✓ | ✓ |
| Compensation | ✓ | ✓ | ✓ | — |
| R&R | ✓ | ✓ | ✓ | — |
| Field verification | ✓ (all) | ✓ (all) | — | ✓ (mine) |
| Alerts | ✓ | ✓ | ✓ | ✓ |
| Reports | ✓ | ✓ | ✓ | — |
| ML insights | ✓ | ✓ | ✓ | — |
| Administration | ✓ | — | — | — |

---

## 5. Responsive / field rules (R12)

- Tailwind breakpoints: `sm` 640, `md` 768, `lg` 1024.
- `AppLayout`: sidebar overlay drawer below `md`; hamburger in `Header`.
- Dashboard: KPI grid 2 cols on phone, 5 on desktop; charts stack.
- Tables: horizontal scroll on phone; Field list uses `Card`.
- Field submit: large tap targets, `input capture="environment"`, GPS button first.
- **No native app.** Same SPA in mobile browser.

---

## 6. Data flow (every page)

```
Page
  ↓ props/state (filters)
api/*.js
  ↓ Authorization: Bearer
FastAPI
  ↓
Service → Repository → PostgreSQL
  ↓ JSON envelope
Page setState
  ↓
presentational components (KpiCard, Table, ParcelMap, …)
```

GIS is the only place Leaflet is imported (`components/map/*`).
Charts are the only place Recharts is imported (`components/dashboard/ChartPanel.jsx`).
