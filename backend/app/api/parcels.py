from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.services.parcels import ParcelService

router = APIRouter(prefix="/parcels", tags=["Parcels"])


@router.get("")
def list_parcels(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ulpin: str | None = None,
    khasra: str | None = None,
    village: str | None = None,
    tehsil: str | None = None,
    state: str | None = None,
    district: str | None = None,
    project_id: UUID | None = None,
    status: str | None = None,
    stage: str | None = None,
):
    page, page_size = clamp_page(page, page_size)
    data, total = ParcelService(db).list_parcels(
        user,
        ulpin=ulpin,
        khasra=khasra,
        village=village,
        tehsil=tehsil,
        state=state,
        district=district,
        project_id=project_id,
        status=status,
        stage=stage,
        page=page,
        page_size=page_size,
    )
    return envelope(data, page=page, page_size=page_size, total=total)


@router.get("/{parcel_id}")
def get_parcel(
    parcel_id: UUID,
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
):
    return envelope(ParcelService(db).get(user, parcel_id))
