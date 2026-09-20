# NLAMP Session Memory

## Purpose

This file contains temporary information for the current AI coding session.

It should remain short.

Do not duplicate AI_BRAIN.md.

## Current Project State

- Repository root: `C:\Users\bhanu\OneDrive\Desktop\sih`
- Main branch is the stable baseline.
- GitHub remote is configured.
- The project currently has frontend, backend, PostgreSQL/PostGIS, GIS, workflow, RBAC, ML, testing, and mock integration functionality.

## Current Priority

Use this file for the active task only.

Examples:

- current feature being implemented
- files currently being modified
- known bug
- test currently failing
- temporary implementation decision
- next immediate action

## Completed Task: National Acquisition Pulse

- Added `NationalAcquisitionPulse` section to `DashboardPage.jsx`.
- Reuses existing `kpis` + `ml` API state — no new endpoints, no new dependencies.
- Six headline metrics: Active projects, Land acquired, Compensation disbursed %, Delayed projects, High delay risk (Prototype Risk Index), R&R complete.
- Disbursement rate is a derived metric computed client-side from existing `kpis.compensation_paid_inr / kpis.compensation_assessed_inr`.
- Loading skeletons, null-safe values, and semantic HTML (`<section aria-label>`, `id`/`aria-labelledby`) all implemented.
- `npm run lint` → 0 errors. `npm run build` → exit 0, ✓ 8.36s.
- No backend, database, migration, RBAC, or API contract changes made.

## Session Rules

When a task is completed:

1. remove obsolete notes
2. update remaining notes if necessary
3. do not turn this file into permanent architecture documentation