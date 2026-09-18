from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, OfficerOps
from app.models.user import User
from app.schemas.common import envelope
from app.schemas.workflow import RehabCreate, RehabUpdate
from app.services.rr import RRService

router = APIRouter(prefix="/rehabilitation", tags=["Rehabilitation"])


@router.get("/{case_id}")
def get_rehab(case_id: UUID, user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(RRService(db).rehabilitation_for_case(user, case_id))


@router.post("", status_code=201)
def create_rehab(body: RehabCreate, user: User = Depends(OfficerOps), db: Session = Depends(get_db)):
    return envelope(RRService(db).create_rehab(user, body))


@router.patch("/{rec_id}")
def patch_rehab(
    rec_id: UUID,
    body: RehabUpdate,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(RRService(db).patch_rehab(user, rec_id, body))
