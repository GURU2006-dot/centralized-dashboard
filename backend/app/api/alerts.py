from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AdminOnly, AnyReader
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.services.alerts import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
def list_alerts(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread: bool | None = None,
):
    page, page_size = clamp_page(page, page_size)
    rows, total = AlertService(db).list_for(user, unread=unread, page=page, page_size=page_size)
    data = [
        {
            "id": r.id,
            "rule_code": r.rule_code,
            "alert_type": r.alert_type,
            "severity": r.severity,
            "message": r.message,
            "project_id": r.project_id,
            "parcel_id": r.parcel_id,
            "acquisition_case_id": r.acquisition_case_id,
            "is_read": r.is_read,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return envelope(data, page=page, page_size=page_size, total=total)


@router.post("/evaluate")
def evaluate_alerts(user: User = Depends(AdminOnly), db: Session = Depends(get_db)):
    created = AlertService(db).evaluate()
    db.commit()
    return envelope({"created": created})


@router.patch("/{alert_id}/read")
def read_alert(alert_id: UUID, user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    row = AlertService(db).mark_read(user, alert_id)
    db.commit()
    return envelope({"id": row.id, "is_read": row.is_read})
