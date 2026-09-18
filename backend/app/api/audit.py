from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AdminOnly
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("")
def list_audit(
    user: User = Depends(AdminOnly),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
):
    page, page_size = clamp_page(page, page_size)
    rows, total = AuditService(db).list_logs(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        page=page,
        page_size=page_size,
    )
    data = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "occurred_at": r.occurred_at,
            "metadata": r.extra_metadata,
        }
        for r in rows
    ]
    return envelope(data, page=page, page_size=page_size, total=total)
