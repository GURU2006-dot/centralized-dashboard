"""Acquisition-case stage catalogue helpers.

Proposal approval is NOT a case stage. Cases use the Phase 1 catalogue.
API alias: R_AND_R → REHABILITATION_RESETTLEMENT.
"""

from __future__ import annotations

from app.models.enums import WORKFLOW_STAGE_CODES

STAGE_SEQUENCE: tuple[str, ...] = WORKFLOW_STAGE_CODES
INITIAL_STAGE = "SIA"

_ALIASES = {
    "R_AND_R": "REHABILITATION_RESETTLEMENT",
    "RR": "REHABILITATION_RESETTLEMENT",
    "R&R": "REHABILITATION_RESETTLEMENT",
}


def normalize_stage(code: str) -> str:
    raw = (code or "").strip().upper()
    return _ALIASES.get(raw, raw)


def next_stage(current: str) -> str | None:
    current = normalize_stage(current)
    if current not in STAGE_SEQUENCE:
        return None
    idx = STAGE_SEQUENCE.index(current)
    if idx >= len(STAGE_SEQUENCE) - 1:
        return None
    return STAGE_SEQUENCE[idx + 1]


def is_terminal(current: str) -> bool:
    return normalize_stage(current) == "COMPLETED"
