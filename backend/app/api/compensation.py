from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, OfficerOps
from app.models.user import User
from app.schemas.common import envelope
from app.schemas.workflow import CompensationCreate, CompensationUpdate
from app.services.compensation import CompensationService

router = APIRouter(prefix="/compensation", tags=["Compensation"])


@router.get("/{case_id}")
def get_compensation(case_id: UUID, user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(CompensationService(db).get(user, case_id))


@router.post("", status_code=201)
def create_compensation(
    body: CompensationCreate,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(CompensationService(db).create(user, body))


@router.patch("/{case_id}")
def patch_compensation(
    case_id: UUID,
    body: CompensationUpdate,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(CompensationService(db).update(user, case_id, body))
