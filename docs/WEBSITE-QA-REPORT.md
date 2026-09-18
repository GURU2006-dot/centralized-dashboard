# NLAMP Website QA Report

**Test date:** 2026-09-11  
**Environment:** Local Vite frontend at `http://127.0.0.1:5173`, FastAPI API at `http://127.0.0.1:8000`, seeded synthetic PostgreSQL/PostGIS data  
**Scope:** Authentication, route rendering, role-aware navigation, mobile layout, proposal validation, GIS behavior, build quality, lint, and backend regression tests

## Executive Summary

The application is usable as a synthetic demonstration: the documented admin login works, the dashboard loads API data, all 24 primary routes rendered content, mobile pages did not horizontally overflow at 375px, the frontend production build succeeded, and the backend suite passed 54 tests.

It is not yet production-ready. The highest-priority issues are the GIS map's reliance on external OpenStreetMap tiles without a visible fallback, a large single frontend bundle, weak user feedback around form validation/loading failures, and a set of lint warnings that indicate fragile effect dependencies and maintainability risk.

## Findings

### High priority

1. **GIS tiles fail without a user-facing fallback.**
   - **Evidence:** Route smoke testing reached `/map`, but every observed OpenStreetMap tile request failed in the test environment.
   - **Impact:** Users can see an empty or incomplete map even though the GeoJSON API returns data. This makes a core spatial workflow unreliable on restricted networks, offline demos, or government networks with outbound tile access blocked.
   - **Improve:** Host approved tiles or use an approved internal tile service, add a map status/error state, and provide a table/list fallback for the parcel geometries.

2. **The frontend ships a large initial JavaScript bundle.**
   - **Evidence:** `vite build` succeeded with a 929.88 kB minified JavaScript asset and emitted a chunk-size warning above 500 kB.
   - **Impact:** Slower first load on field devices and constrained networks.
   - **Improve:** Lazy-load route pages, especially GIS, charts, and reports; split vendor-heavy modules; measure the largest contributors with a bundle analyzer.

### Medium priority

3. **Form validation feedback is not explicit enough.**
   - **Evidence:** Submitting the empty new-proposal form kept the user on `/proposals/new` through native required-field validation, but no visible inline summary or explanatory message appeared in the tested rendered state.
   - **Impact:** Users may not know which fields are required or why submission did not proceed, especially on mobile or assistive technology.
   - **Improve:** Add visible field-level error text, an error summary linked to invalid fields, numeric upper bounds, and a clear “select at least one parcel” rule if the backend requires it.

4. **Error states are too quiet on data-loading failures.**
   - **Evidence:** Several page effects catch request failures and leave the page in an empty/default state; the GIS page also suppresses the filter and GeoJSON request error paths.
   - **Impact:** A network or API failure can look like “no data” rather than an actionable outage.
   - **Improve:** Show retryable error banners/toasts with the affected operation, preserve the last successful data, and distinguish empty results from failed requests.

5. **Lint reports multiple React effect dependency and state-in-effect warnings.**
   - **Evidence:** `npm run lint` reported warnings in proposal, project, parcel, dashboard, GIS, acquisition, document, family, alert, notification, and auth code. It also reported an unused `getPredictionHistory` import.
   - **Impact:** Stale closures, redundant renders, or missed reloads may appear as the app grows, and warnings can hide real regressions.
   - **Improve:** Resolve warnings in small batches, starting with missing `load`/`toast` dependencies and the unused import; use event-driven updates or derived state where appropriate.

6. **Settings is exposed to every role.**
   - **Evidence:** `visibleNav()` assigns `roles: null` to `/settings`; the stable officer probe also loaded the settings route while admin-only users, audit, and integrations were blocked by the role gate.
   - **Impact:** This may be correct for personal settings, but it is a privilege risk if the screen later gains system-wide configuration controls.
   - **Improve:** Split personal profile/preferences from system settings and gate the latter explicitly to administrators.

### Low priority

7. **Status badge configuration contains a duplicate `SUBMITTED` key.**
   - **Evidence:** `npm run lint` reported a duplicate object key in `src/components/ui.jsx`.
   - **Impact:** One value silently overwrites another and makes status styling harder to reason about.
   - **Improve:** Keep one canonical mapping and add a small test for all API status values.

8. **The application is not yet tested across browser/network conditions.**
   - **Evidence:** This pass used the integrated Chromium browser at desktop and 375px mobile dimensions. It did not establish coverage for Safari, Firefox, keyboard-only navigation, screen readers, slow 3G, or offline recovery.
   - **Improve:** Add a repeatable Playwright matrix for viewport, role, API failure, and network throttling; run an accessibility audit and keyboard traversal test in CI.

## Tests Performed

| Area | Result |
| --- | --- |
| Admin login with `admin@demo.local` / documented demo password | Passed |
| Dashboard API data rendering | Passed; dashboard showed seeded metrics and charts |
| Primary route smoke test | Passed; 24 routes rendered non-empty content with expected headings |
| Mobile layout at 375px viewport | Passed for tested routes; no horizontal overflow detected |
| Mobile navigation drawer | Passed; opens and exposes labeled navigation links |
| Empty proposal submission | Blocked by required-field validation; feedback should be made more explicit |
| Officer role route gate | Passed for tested admin-only/field-only routes; proposal, document, acquisition, and compensation routes remained available |
| GIS external tile requests | Failed in this environment; all observed tile requests failed |
| Frontend production build | Passed with chunk-size warning |
| Frontend lint | Completed with warnings; see findings |
| Backend regression suite | Passed: 54 tests, 1 dependency deprecation warning |

## Recommended Order of Work

1. Add GIS failure handling and a non-map parcel list/table fallback.
2. Add explicit form and API error states, then test them with mocked failures.
3. Split/lazy-load route bundles and recheck field-device load time.
4. Clear lint warnings, especially effect dependencies and duplicate status keys.
5. Confirm whether settings is personal-only; enforce the intended role policy in both UI and API.
6. Add automated accessibility, keyboard, cross-browser, and network-degradation coverage.

## Overall Assessment

**Demo readiness:** Good.  
**Operational readiness:** Not ready without the GIS fallback, clearer failure states, stronger accessibility/compatibility testing, and bundle/performance work.