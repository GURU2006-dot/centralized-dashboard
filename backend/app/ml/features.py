"""Feature contract shared by training and inference.

All names are derived from the existing NLAMP schema. No PII.
"""

from __future__ import annotations

FEATURE_NAMES: tuple[str, ...] = (
    "current_stage_index",
    "days_since_start",
    "days_in_current_stage",
    "workflow_event_count",
    "completed_stage_count",
    "remaining_stage_count",
    "compensation_assessed",
    "compensation_paid_ratio",
    "unpaid_balance",
    "field_verification_done",
    "field_checks_complete",
    "gps_available",
    "document_count",
    "unverified_document_count",
    "affected_family_count",
    "displaced_family_count",
    "project_area_ha",
    "parcel_area_ha",
    "project_is_delayed",
)

STAGE_INDEX = {
    "SIA": 1,
    "NOTIFICATION": 2,
    "AWARD": 3,
    "COMPENSATION_ASSESSMENT": 4,
    "COMPENSATION_PAID": 5,
    "POSSESSION": 6,
    "REHABILITATION_RESETTLEMENT": 7,
    "COMPLETED": 8,
}

N_STAGES = 8
MODEL_NAME = "random_forest_delay_risk"
MODEL_VERSION = "rf-delay-v1"
RANDOM_STATE = 42

# Prototype display conventions (not government standards).
# Stored DB risk_score remains 0–1 (class-midpoint index / 100). Display score = that value × 100.
LOW_MAX = 39
MEDIUM_MAX = 69


def vector_from_dict(features: dict) -> list[float]:
    row = []
    for name in FEATURE_NAMES:
        value = features.get(name, 0)
        if value is None:
            value = 0
        row.append(float(value))
    return row


def score_100(p_high: float) -> float:
    """Legacy helper: map a 0–1 value onto 0–100. Prefer class-midpoint index in predictor."""
    p = max(0.0, min(1.0, float(p_high)))
    return round(p * 100.0, 1)


def category_from_score_100(score: float) -> str:
    if score <= LOW_MAX:
        return "LOW"
    if score <= MEDIUM_MAX:
        return "MEDIUM"
    return "HIGH"


def risk_indicators(features: dict) -> list[str]:
    """Feature-based observations. Not causal explanations."""
    notes: list[str] = []
    days = float(features.get("days_in_current_stage") or 0)
    if days >= 21:
        notes.append(f"{int(days)} days in current stage")
    ratio = float(features.get("compensation_paid_ratio") or 0)
    if ratio < 0.6:
        notes.append(f"Compensation only {int(ratio * 100)}% paid")
    if float(features.get("field_verification_done") or 0) < 1:
        notes.append("Field verification incomplete")
    unverified = int(features.get("unverified_document_count") or 0)
    if unverified > 0:
        notes.append(f"{unverified} document(s) pending verification")
    if float(features.get("gps_available") or 0) < 1:
        notes.append("GPS not captured")
    displaced = int(features.get("displaced_family_count") or 0)
    if displaced > 0 and float(features.get("remaining_stage_count") or 0) > 2:
        notes.append(f"{displaced} displaced families with remaining workflow")
    if float(features.get("project_is_delayed") or 0) >= 1:
        notes.append("Project status is DELAYED")
    remaining = int(features.get("remaining_stage_count") or 0)
    if remaining >= 5:
        notes.append(f"{remaining} stages remaining")
    return notes[:6]
