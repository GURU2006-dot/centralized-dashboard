from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, OfficerOps
from app.models.user import User
from app.schemas.common import envelope
from app.schemas.workflow import PossessionCreate, PossessionUpdate
from app.services.possession import PossessionService

router = APIRouter(prefix="/possession", tags=["Possession"])


@router.get("/{case_id}")
def get_possession(case_id: UUID, user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(PossessionService(db).get(user, case_id))


@router.post("", status_code=201)
def create_possession(
    body: PossessionCreate,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(PossessionService(db).create(user, body))


@router.patch("/{case_id}")
def patch_possession(
    case_id: UUID,
    body: PossessionUpdate,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(PossessionService(db).update(user, case_id, body))
