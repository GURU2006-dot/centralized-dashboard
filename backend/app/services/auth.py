from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.errors import AppError
from app.logging import get_logger
from app.models.user import User
from app.repositories.users import UserRepository
from app.security import (
    access_token_expires_seconds,
    create_access_token,
    verify_password,
)

log = get_logger("nlamp.auth")


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def login(self, email: str, password: str) -> dict:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            log.info("Authentication failure for email=%s", email.strip().lower())
            raise AppError(401, "INVALID_CREDENTIALS", "Invalid email or password")
        if not user.is_active:
            raise AppError(403, "ACCOUNT_DISABLED", "Account is disabled")
        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        token = create_access_token(user_id=user.id, role=user.role.code)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": access_token_expires_seconds(),
            "user": self.to_public(user),
        }

    @staticmethod
    def to_public(user: User) -> dict:
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.code,
            "state_code": user.state_code,
            "district_code": user.district_code,
            "is_active": user.is_active,
        }
