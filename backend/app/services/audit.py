from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        user: User | None,
        action: str,
        entity_type: str,
        entity_id: UUID | str,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        meta = dict(details or {})
        if user and user.role:
            meta.setdefault("role", user.role.code)
        row = AuditLog(
            user_id=user.id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            extra_metadata=meta,
        )
        self.db.add(row)
        return row

    def list_logs(
        self,
        *,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        from sqlalchemy import func, select

        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(AuditLog.occurred_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return rows, int(total)
