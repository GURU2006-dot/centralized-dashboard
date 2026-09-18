from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def list_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread: bool | None = None,
):
    page, page_size = clamp_page(page, page_size)
    rows, total = NotificationService(db).list_for(
        user, unread=unread, page=page, page_size=page_size
    )
    data = [
        {
            "id": r.id,
            "title": r.title,
            "body": r.body,
            "related_type": r.related_type,
            "related_id": r.related_id,
            "is_read": r.is_read,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return envelope(data, page=page, page_size=page_size, total=total)


@router.patch("/read-all")
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = NotificationService(db).mark_all_read(user)
    db.commit()
    return envelope({"updated": n})


@router.patch("/{notification_id}/read")
def read_one(
    notification_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = NotificationService(db).mark_read(user, notification_id)
    db.commit()
    return envelope({"id": row.id, "is_read": row.is_read})
