"""Assemble live feature dicts from PostgreSQL. Same names as training."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.features import FEATURE_NAMES, N_STAGES, STAGE_INDEX
from app.models.acquisition import AcquisitionCase, WorkflowEvent
from app.models.compensation import Compensation
from app.models.document import Document
from app.models.family import AffectedFamily
from app.models.field_verification import FieldVerification
from app.models.parcel import LandParcel
from app.models.project import Project


def _days(start, now) -> float:
    if start is None:
        return 0.0
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    return max(0.0, (now - start).total_seconds() / 86400.0)


def assemble_features(db: Session, case: AcquisitionCase) -> dict:
    now = datetime.now(timezone.utc)
    project = case.project or db.get(Project, case.project_id)
    parcel = case.parcel or db.get(LandParcel, case.parcel_id)
    stage_idx = STAGE_INDEX.get(case.current_stage, 1)
    events = db.scalar(
        select(func.count()).select_from(WorkflowEvent).where(
            WorkflowEvent.acquisition_case_id == case.id
        )
    ) or 0
    comp = db.scalars(
        select(Compensation).where(Compensation.acquisition_case_id == case.id)
    ).first()
    assessed = float(comp.assessed_amount_inr or 0) if comp else 0.0
    paid = float(comp.paid_amount_inr or 0) if comp else 0.0
    ratio = (paid / assessed) if assessed > 0 else 0.0
    fv = db.scalars(
        select(FieldVerification).where(FieldVerification.acquisition_case_id == case.id)
    ).first()
    if fv is None and parcel is not None:
        fv = db.scalars(
            select(FieldVerification).where(FieldVerification.parcel_id == parcel.id)
        ).first()
    field_done = 1.0 if fv and fv.status in ("SUBMITTED", "ACCEPTED") else 0.0
    checks = 0.0
    gps = 0.0
    if fv:
        checks = float(
            int(bool(fv.owner_verified))
            + int(bool(fv.land_info_verified))
            + int(bool(fv.documents_verified))
        )
        gps = 1.0 if fv.gps_lat is not None and fv.gps_lng is not None else 0.0
    doc_stmt = select(Document)
    if parcel is not None:
        doc_stmt = doc_stmt.where(
            (Document.acquisition_case_id == case.id) | (Document.parcel_id == parcel.id)
        )
    else:
        doc_stmt = doc_stmt.where(Document.acquisition_case_id == case.id)
    docs = list(db.scalars(doc_stmt).all())
    unverified = sum(1 for d in docs if d.verification_status != "VERIFIED")
    fams = list(
        db.scalars(select(AffectedFamily).where(AffectedFamily.project_id == case.project_id)).all()
    )
    displaced = sum(1 for f in fams if f.is_displaced)
    features = {
        "current_stage_index": float(stage_idx),
        "days_since_start": _days(case.started_at or case.created_at, now),
        "days_in_current_stage": _days(case.stage_entered_at or case.started_at, now),
        "workflow_event_count": float(events),
        "completed_stage_count": float(max(stage_idx - 1, 0)),
        "remaining_stage_count": float(max(N_STAGES - stage_idx, 0)),
        "compensation_assessed": assessed,
        "compensation_paid_ratio": min(max(ratio, 0.0), 1.0),
        "unpaid_balance": max(assessed - paid, 0.0),
        "field_verification_done": field_done,
        "field_checks_complete": checks,
        "gps_available": gps,
        "document_count": float(len(docs)),
        "unverified_document_count": float(unverified),
        "affected_family_count": float(len(fams)),
        "displaced_family_count": float(displaced),
        "project_area_ha": float(project.estimated_area_ha or 0) if project else 0.0,
        "parcel_area_ha": float(parcel.area_ha or 0) if parcel else 0.0,
        "project_is_delayed": 1.0 if project and project.status == "DELAYED" else 0.0,
    }
    return {name: features[name] for name in FEATURE_NAMES}
