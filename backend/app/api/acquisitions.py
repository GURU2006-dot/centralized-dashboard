from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, OfficerOps
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.schemas.workflow import TransitionBody
from app.services.acquisitions import AcquisitionService
from app.workflow.engine import WorkflowService

router = APIRouter(prefix="/acquisitions", tags=["Acquisitions"])


@router.get("")
def list_acquisitions(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_id: UUID | None = None,
    parcel_id: UUID | None = None,
    state: str | None = None,
    district: str | None = None,
    stage: str | None = None,
    status: str | None = None,
    risk_level: str | None = None,
):
    page, page_size = clamp_page(page, page_size)
    data, total = AcquisitionService(db).list_cases(
        user,
        project_id=project_id,
        parcel_id=parcel_id,
        state=state,
        district=district,
        stage=stage,
        status=status,
        risk_level=risk_level,
        page=page,
        page_size=page_size,
    )
    return envelope(data, page=page, page_size=page_size, total=total)


@router.get("/{case_id}")
def get_acquisition(
    case_id: UUID,
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
):
    return envelope(AcquisitionService(db).get(user, case_id))


@router.get("/{case_id}/timeline")
def get_timeline(
    case_id: UUID,
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
):
    return envelope(AcquisitionService(db).timeline(user, case_id))


@router.post("/{case_id}/transition")
def transition_case(
    case_id: UUID,
    body: TransitionBody,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(WorkflowService(db).transition(user, case_id, body.to_stage, body.remarks))
