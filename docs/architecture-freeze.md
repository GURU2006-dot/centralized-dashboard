# Architecture freeze (pre–Phase 1)

Corrections accepted before implementation:

1. **Proposal approval is authoritative.** `proposals.status` (`APPROVED` / `REJECTED`) is the only approval action. Acquisition cases are created only after approval and then follow `SIA → NOTIFICATION → AWARD → COMPENSATION_ASSESSMENT → COMPENSATION_PAID → POSSESSION → REHABILITATION_RESETTLEMENT → COMPLETED`. Case workflow has **no** competing approve/reject.
2. Full API contracts remain the **target**; implement by P0/P1/P2. Phase 1 is database only.
3. `ml_predictions.risk_score` is a **model risk score**, not a calibrated P(delay). `trained_on = SYNTHETIC` plus disclaimer in later UI/API.
4. Owner `id_number`, `phone`, `address` are stored for authorized contexts; they must not appear in general parcel responses (later phases).
5. Government systems stay behind adapters. Phase 1 has **no** adapters, **no** live calls, **no** invented credentials.

Phase 1 does not implement FastAPI routers, React, ML training, or auth UI.
