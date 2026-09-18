from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, ProjectWriter
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.schemas.projects import ProjectCreate, ProjectUpdate
from app.services.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("")
def list_projects(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    state: str | None = None,
    district: str | None = None,
    status: str | None = None,
    stage: str | None = None,
):
    page, page_size = clamp_page(page, page_size)
    data, total = ProjectService(db).list_projects(
        user,
        search=search,
        state=state,
        district=district,
        status=status,
        stage=stage,
        page=page,
        page_size=page_size,
    )
    return envelope(data, page=page, page_size=page_size, total=total)


@router.get("/{project_id}")
def get_project(
    project_id: UUID,
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
):
    return envelope(ProjectService(db).get(user, project_id))


@router.post("", status_code=201)
def create_project(
    body: ProjectCreate,
    user: User = Depends(ProjectWriter),
    db: Session = Depends(get_db),
):
    return envelope(ProjectService(db).create(user, body))


@router.patch("/{project_id}")
def patch_project(
    project_id: UUID,
    body: ProjectUpdate,
    user: User = Depends(ProjectWriter),
    db: Session = Depends(get_db),
):
    return envelope(ProjectService(db).update(user, project_id, body))
