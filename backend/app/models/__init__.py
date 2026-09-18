"""Import all models so Alembic and metadata.create_all see every table."""

from app.models.alert import Alert
from app.models.acquisition import AcquisitionCase, WorkflowEvent, WorkflowStageDefinition
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.compensation import Compensation
from app.models.document import Document
from app.models.family import AffectedFamily, Rehabilitation, Resettlement
from app.models.field_verification import FieldVerification
from app.models.geo import District, State
from app.models.ml_prediction import MLPrediction
from app.models.notification import Notification
from app.models.parcel import LandParcel, Owner, ParcelOwner
from app.models.possession import Possession
from app.models.project import Project
from app.models.proposal import Proposal, ProposalParcel
from app.models.user import Role, User

__all__ = [
    "Base",
    "Role",
    "User",
    "State",
    "District",
    "Project",
    "LandParcel",
    "Owner",
    "ParcelOwner",
    "Proposal",
    "ProposalParcel",
    "WorkflowStageDefinition",
    "AcquisitionCase",
    "WorkflowEvent",
    "Document",
    "Compensation",
    "AffectedFamily",
    "Rehabilitation",
    "Resettlement",
    "Possession",
    "FieldVerification",
    "Notification",
    "Alert",
    "MLPrediction",
    "AuditLog",
]
