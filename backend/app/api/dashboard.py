from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader
from app.models.user import User
from app.schemas.common import envelope
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis")
def kpis(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    state: str | None = None,
    district: str | None = None,
    project_id: UUID | None = None,
    stage: str | None = None,
    status: str | None = None,
):
    data = DashboardService(db).kpis(
        user,
        state=state,
        district=district,
        project_id=project_id,
        stage=stage,
        status=status,
    )
    return envelope(data, filters_applied={"state": state, "district": district, "project_id": str(project_id) if project_id else None, "stage": stage, "status": status})


@router.get("/charts")
def charts(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    state: str | None = None,
    district: str | None = None,
    project_id: UUID | None = None,
    stage: str | None = None,
    status: str | None = None,
):
    data = DashboardService(db).charts(
        user,
        state=state,
        district=district,
        project_id=project_id,
        stage=stage,
        status=status,
    )
    return envelope(data)


@router.get("/filters")
def filters(user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(DashboardService(db).filters(user))
