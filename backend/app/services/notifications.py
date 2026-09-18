from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.notification import Notification
from app.models.user import User
from app.repositories.users import UserRepository


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def notify(
        self,
        user_id: UUID,
        title: str,
        body: str,
        related_type: str | None = None,
        related_id: str | None = None,
    ) -> Notification:
        row = Notification(
            id=uuid4(),
            user_id=user_id,
            title=title,
            body=body,
            channel="IN_APP",
            related_type=related_type,
            related_id=related_id,
            is_read=False,
            data_source="SYNTHETIC",
        )
        self.db.add(row)
        return row

    def notify_roles(
        self,
        role_codes: list[str],
        title: str,
        body: str,
        related_type: str | None = None,
        related_id: str | None = None,
        exclude_user_id: UUID | None = None,
    ) -> None:
        repo = UserRepository(self.db)
        seen: set[UUID] = set()
        for code in role_codes:
            for user in repo.list_by_role(code):
                if exclude_user_id and user.id == exclude_user_id:
                    continue
                if user.id in seen:
                    continue
                seen.add(user.id)
                self.notify(user.id, title, body, related_type, related_id)

    def list_for(self, user: User, *, unread: bool | None, page: int, page_size: int):
        stmt = select(Notification).where(Notification.user_id == user.id)
        if unread:
            stmt = stmt.where(Notification.is_read.is_(False))
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(Notification.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return rows, int(total)

    def mark_read(self, user: User, notification_id: UUID) -> Notification:
        row = self.db.scalars(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user.id
            )
        ).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Notification not found")
        row.is_read = True
        return row

    def mark_all_read(self, user: User) -> int:
        result = self.db.execute(
            update(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        return result.rowcount or 0
