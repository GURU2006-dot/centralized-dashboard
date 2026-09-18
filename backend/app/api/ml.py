from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, require_roles
from app.models.user import User
from app.schemas.common import envelope
from app.services.ml import MLService

router = APIRouter(prefix="/ml", tags=["Machine Learning"])
PredictOps = require_roles("ADMIN", "ACQUISITION_OFFICER", "APPROVING_AUTHORITY")


class BatchBody(BaseModel):
    project_id: UUID | None = None
    limit: int = 40


@router.get("/metrics")
def metrics(user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(MLService(db).metrics())


@router.get("/summary")
def summary(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    project_id: UUID | None = None,
):
    return envelope(MLService(db).summary(user, project_id=project_id))


@router.get("/analytics")
def analytics(user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(MLService(db).analytics(user))


@router.get("/predictions/{case_id}")
def history(case_id: UUID, user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(MLService(db).history(user, case_id))


@router.post("/predict/batch")
def batch(body: BatchBody, user: User = Depends(PredictOps), db: Session = Depends(get_db)):
    return envelope(MLService(db).predict_batch(user, project_id=body.project_id, limit=body.limit))


@router.post("/predict/{case_id}")
def predict(case_id: UUID, user: User = Depends(PredictOps), db: Session = Depends(get_db)):
    return envelope(MLService(db).predict_case(user, case_id))
