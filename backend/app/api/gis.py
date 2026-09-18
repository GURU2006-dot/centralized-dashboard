from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader
from app.models.user import User
from app.schemas.common import envelope
from app.services.gis import GISService

router = APIRouter(prefix="/gis", tags=["GIS"])


@router.get("/parcels")
def parcel_geojson(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    state: str | None = None,
    district: str | None = None,
    project_id: UUID | None = None,
    status: str | None = None,
    stage: str | None = None,
    risk_level: str | None = None,
    limit: int = Query(80, ge=1, le=120),
):
    return envelope(
        GISService(db).parcel_features(
            user,
            state=state,
            district=district,
            project_id=project_id,
            status=status,
            stage=stage,
            risk_level=risk_level,
            limit=limit,
        )
    )
