from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(func.lower(User.email) == email.strip().lower())
        )
        return self.db.scalars(stmt).first()

    def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
        return self.db.scalars(stmt).first()

    def list_by_role(self, role_code: str) -> list[User]:
        from app.models.user import Role

        stmt = (
            select(User)
            .options(selectinload(User.role))
            .join(Role, User.role_id == Role.id)
            .where(Role.code == role_code, User.is_active.is_(True))
        )
        return list(self.db.scalars(stmt).all())
