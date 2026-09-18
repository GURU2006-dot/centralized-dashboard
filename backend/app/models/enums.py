"""String enumerations used in CHECK constraints. Not PostgreSQL ENUM types."""

from __future__ import annotations

from enum import StrEnum


class DataSource(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    MOCK_ADAPTER = "MOCK_ADAPTER"
    EXTERNAL = "EXTERNAL"


class RoleCode(StrEnum):
    ADMIN = "ADMIN"
    ACQUISITION_OFFICER = "ACQUISITION_OFFICER"
    APPROVING_AUTHORITY = "APPROVING_AUTHORITY"
    FIELD_OFFICER = "FIELD_OFFICER"


class ProjectStatus(StrEnum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    DELAYED = "DELAYED"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"


class AcquisitionStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROCESS = "IN_PROCESS"
    ACQUIRED = "ACQUIRED"
    DISPUTED = "DISPUTED"
    DROPPED = "DROPPED"


class OwnershipType(StrEnum):
    SOLE = "SOLE"
    JOINT = "JOINT"
    LEGAL_HEIR = "LEGAL_HEIR"
    ENCUMBERED = "ENCUMBERED"


class ProposalStatus(StrEnum):
    """Authoritative approval lives here — NOT on acquisition_cases."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_VERIFICATION = "UNDER_VERIFICATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CaseStatus(StrEnum):
    OPEN = "OPEN"
    ON_HOLD = "ON_HOLD"
    CLOSED = "CLOSED"
    DROPPED = "DROPPED"


class DocumentType(StrEnum):
    LAND_RECORD = "LAND_RECORD"
    SIA_REPORT = "SIA_REPORT"
    OWNERSHIP_PROOF = "OWNERSHIP_PROOF"
    COMPENSATION = "COMPENSATION"
    AWARD = "AWARD"
    RR = "RR"
    PHOTO = "PHOTO"
    OTHER = "OTHER"


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class CompensationStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    ASSESSED = "ASSESSED"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    DISPUTED = "DISPUTED"


class FamilyStatus(StrEnum):
    IDENTIFIED = "IDENTIFIED"
    ASSISTED = "ASSISTED"
    RESETTLED = "RESETTLED"
    CLOSED = "CLOSED"


class RehabStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ResettlementStatus(StrEnum):
    NOT_ALLOTTED = "NOT_ALLOTTED"
    ALLOTTED = "ALLOTTED"
    POSSESSED = "POSSESSED"


class PossessionStatus(StrEnum):
    NOT_TAKEN = "NOT_TAKEN"
    PARTIAL = "PARTIAL"
    TAKEN = "TAKEN"


class FieldVerificationStatus(StrEnum):
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class AlertSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TrainedOn(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    AUTHORIZED_HISTORICAL = "AUTHORIZED_HISTORICAL"


# Post-proposal acquisition lifecycle only.
# Proposal approval (proposals.status) is the sole approval action.
WORKFLOW_STAGE_CODES = (
    "SIA",
    "NOTIFICATION",
    "AWARD",
    "COMPENSATION_ASSESSMENT",
    "COMPENSATION_PAID",
    "POSSESSION",
    "REHABILITATION_RESETTLEMENT",
    "COMPLETED",
)
