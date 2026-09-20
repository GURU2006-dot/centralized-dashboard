# NLAMP AI Coding Rules

## Rule 1 — Inspect Before Editing

Before changing code:

- identify the relevant feature
- identify its frontend/backend path
- inspect the existing implementation
- inspect related tests

Do not edit based only on filenames or assumptions.

## Rule 2 — Minimal Context

Only inspect files relevant to the requested task.

Do not scan the complete repository unless the task genuinely requires repository-wide analysis.

Prefer:

task
→ relevant page/component/API
→ relevant backend endpoint/service
→ relevant test
→ change

## Rule 3 — Preserve Architecture

Do not replace existing architecture unless explicitly requested.

Preserve:

- React/Vite
- FastAPI
- PostgreSQL/PostGIS
- SQLAlchemy
- Alembic
- JWT/RBAC
- Leaflet
- existing API client
- existing workflow engine
- lazy route loading
- existing test structure

## Rule 4 — Business Rules Are Immutable Unless Explicitly Changed

Do not change these accidentally:

- proposal approval is authoritative
- approval creates acquisition cases
- no second acquisition-case approval
- workflow stage ordering
- workflow stage gates
- geographic authorization
- PII protection
- mock-only government integrations
- synthetic-data disclaimer
- prototype risk-index semantics

If a requested feature conflicts with one of these rules, stop and explain the conflict before implementing it.

## Rule 5 — Backend Is the Security Boundary

Never rely on frontend hiding alone for authorization.

Any permission-sensitive operation must be enforced by backend RBAC/scoping.

## Rule 6 — API Compatibility

Before changing an API:

1. inspect the endpoint
2. inspect its schema
3. inspect frontend consumers
4. inspect relevant tests

Avoid breaking response contracts.

## Rule 7 — Validation Must Not Be Weakened

Never weaken validation simply to make tests pass.

If a test fails because the requirement is incorrect, investigate the implementation and requirement instead.

Do not change strict assertions to broad assertions without a justified reason.

## Rule 8 — Error and Loading States

New frontend API interactions should account for:

- loading
- success
- empty state
- API failure
- retry/recovery where appropriate
- mutation busy state
- duplicate submission prevention where applicable

## Rule 9 — Accessibility

Preserve existing accessibility work.

Use:

- semantic HTML
- labels
- accessible names
- keyboard navigation
- focus-visible states
- appropriate ARIA only where needed

Do not add unnecessary ARIA attributes.

## Rule 10 — GIS Safety

Do not expose sensitive owner information through public GIS/parcel APIs.

Preserve map error handling, empty states, filters, and role-based geographic scope.

## Rule 11 — ML Terminology

Use:

"Prototype Risk Index"

Do not describe it as a calibrated probability unless the model has actually been recalibrated and validated.

## Rule 12 — Synthetic Data

Never present synthetic prototype records as real government land records or live cadastral data.

Preserve the project disclaimer.

## Rule 13 — Government Integrations

Government integrations are mock adapters.

Never imply that the prototype is connected to live government systems.

## Rule 14 — Dependencies

Do not install new dependencies unless necessary.

Before adding one, check whether the existing stack already provides the required capability.

## Rule 15 — File Changes

Avoid unrelated formatting or refactoring.

Every modified file should have a reason connected to the requested task.

## Rule 16 — Testing

After changes:

1. run targeted tests
2. run relevant build/lint checks
3. run broader tests when the change is cross-cutting

Do not claim a test passed unless it was actually run.

## Rule 17 — Failure Recovery

If a command fails:

- read the error
- determine the root cause
- avoid random fixes
- do not modify unrelated configuration merely to bypass the failure

## Rule 18 — Environment Configuration

Never assume a fixed database port or environment-specific configuration.

Use the current project configuration and runtime environment.

## Rule 19 — Git Safety

Do not:

- force-push
- reset/delete user work
- rewrite history
- remove unrelated changes

unless explicitly instructed.

Prefer small, reviewable commits.

## Rule 20 — Final Response

After completing a task, report:

- what changed
- files changed
- tests/checks actually run
- remaining warnings/issues
- anything requiring human review

Do not claim production readiness unless it has actually been demonstrated.