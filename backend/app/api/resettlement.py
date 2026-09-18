from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, OfficerOps
from app.models.user import User
from app.schemas.common import envelope
from app.schemas.workflow import ResetCreate, ResetUpdate
from app.services.rr import RRService

router = APIRouter(prefix="/resettlement", tags=["Resettlement"])


@router.get("/{case_id}")
def get_reset(case_id: UUID, user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(RRService(db).resettlement_for_case(user, case_id))


@router.post("", status_code=201)
def create_reset(body: ResetCreate, user: User = Depends(OfficerOps), db: Session = Depends(get_db)):
    return envelope(RRService(db).create_reset(user, body))


@router.patch("/{rec_id}")
def patch_reset(
    rec_id: UUID,
    body: ResetUpdate,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(RRService(db).patch_reset(user, rec_id, body))
