from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import Approver, ProposalReader, ProposalWriter
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.schemas.workflow import ProposalCreate, ProposalUpdate, RejectBody, RemarksBody
from app.services.proposals import ProposalService

router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.post("", status_code=201)
def create_proposal(
    body: ProposalCreate,
    user: User = Depends(ProposalWriter),
    db: Session = Depends(get_db),
):
    return envelope(ProposalService(db).create(user, body))


@router.get("")
def list_proposals(
    user: User = Depends(ProposalReader),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    project_id: UUID | None = None,
):
    page, page_size = clamp_page(page, page_size)
    data, total = ProposalService(db).list_proposals(
        user, status=status, project_id=project_id, page=page, page_size=page_size
    )
    return envelope(data, page=page, page_size=page_size, total=total)


@router.get("/{proposal_id}")
def get_proposal(
    proposal_id: UUID,
    user: User = Depends(ProposalReader),
    db: Session = Depends(get_db),
):
    return envelope(ProposalService(db).get(user, proposal_id))


@router.patch("/{proposal_id}")
def patch_proposal(
    proposal_id: UUID,
    body: ProposalUpdate,
    user: User = Depends(ProposalWriter),
    db: Session = Depends(get_db),
):
    return envelope(ProposalService(db).update(user, proposal_id, body))


@router.post("/{proposal_id}/submit")
def submit_proposal(
    proposal_id: UUID,
    body: RemarksBody | None = None,
    user: User = Depends(ProposalWriter),
    db: Session = Depends(get_db),
):
    return envelope(ProposalService(db).submit(user, proposal_id, body.remarks if body else None))


@router.post("/{proposal_id}/verify")
def verify_proposal(
    proposal_id: UUID,
    body: RemarksBody | None = None,
    user: User = Depends(ProposalWriter),
    db: Session = Depends(get_db),
):
    return envelope(ProposalService(db).verify(user, proposal_id, body.remarks if body else None))


@router.post("/{proposal_id}/approve")
def approve_proposal(
    proposal_id: UUID,
    body: RemarksBody | None = None,
    user: User = Depends(Approver),
    db: Session = Depends(get_db),
):
    return envelope(ProposalService(db).approve(user, proposal_id, body.remarks if body else None))


@router.post("/{proposal_id}/reject")
def reject_proposal(
    proposal_id: UUID,
    body: RejectBody,
    user: User = Depends(Approver),
    db: Session = Depends(get_db),
):
    return envelope(ProposalService(db).reject(user, proposal_id, body.remarks))
