from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, OfficerOps
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.schemas.workflow import FamilyCreate, FamilyUpdate
from app.services.families import FamilyService

router = APIRouter(prefix="/families", tags=["Families"])


@router.get("")
def list_families(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_id: UUID | None = None,
):
    page, page_size = clamp_page(page, page_size)
    data, total = FamilyService(db).list_families(
        user, project_id=project_id, page=page, page_size=page_size
    )
    return envelope(data, page=page, page_size=page_size, total=total)


@router.get("/{family_id}")
def get_family(family_id: UUID, user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(FamilyService(db).get(user, family_id))


@router.post("", status_code=201)
def create_family(
    body: FamilyCreate, user: User = Depends(OfficerOps), db: Session = Depends(get_db)
):
    return envelope(FamilyService(db).create(user, body))


@router.patch("/{family_id}")
def patch_family(
    family_id: UUID,
    body: FamilyUpdate,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(FamilyService(db).update(user, family_id, body))
