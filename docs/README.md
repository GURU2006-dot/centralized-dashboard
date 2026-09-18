# SIH 26016 — Architecture Artifacts

**Problem:** National Land Acquisition Management & Intelligence Platform  
**Event:** Smart India Hackathon 2026 — Problem Statement 26016  
**Scope:** One-day demonstrable MVP architecture  
**Status:** Architecture complete. **No application code in this phase.**

This folder contains **only** the artifacts required by §23 of the specification.

| Artifact | File |
|---|---|
| Spec analysis | [00-analysis.md](./00-analysis.md) |
| A. Repository structure | [A-repository-structure.md](./A-repository-structure.md) |
| B. Database ERD | [B-database-erd.md](./B-database-erd.md) |
| C. API contracts | [C-api-contracts.md](./C-api-contracts.md) |
| D. Frontend component hierarchy | [D-frontend-component-hierarchy.md](./D-frontend-component-hierarchy.md) |
| E. ML interface | [E-ml-interface.md](./E-ml-interface.md) |
| F. Integration interfaces | [F-integration-interfaces.md](./F-integration-interfaces.md) |
| G. Authentication / RBAC | [G-auth-rbac.md](./G-auth-rbac.md) |
| H. Implementation plan | [H-implementation-plan.md](./H-implementation-plan.md) |
| I. One-day execution plan | [I-one-day-execution-plan.md](./I-one-day-execution-plan.md) |
| J. Architecture decisions | [J-architecture-decisions.md](./J-architecture-decisions.md) |

## Hard rules carried into every artifact

1. No application code in this phase.
2. No invented live government APIs.
3. No assumed access to government databases.
4. Synthetic/demo data is labelled `SYNTHETIC` / `MOCK` and is never presented as live cadastral or DoLR data.
5. Modular monolith: frontend, backend, database, ML, integrations stay separate modules inside **one** deployable backend and **one** SPA.
6. No microservices, no blockchain, no extra AI features.
7. P0 must be demoable in one day; P2 is architecture/demo-only.

## Prototype data disclaimer (must appear in UI)

> All projects, parcels, owners, geometries, compensation figures, and ML scores in this prototype are **synthetic demonstration data**. They are **not** live land records, cadastral maps, or government statistics.
