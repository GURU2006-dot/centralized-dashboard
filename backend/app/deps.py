"""FastAPI dependencies: DB session, current user, RBAC."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import AppError
from app.models.user import User
from app.repositories.users import UserRepository
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise AppError(401, "UNAUTHORIZED", "Authentication required")
    payload = decode_access_token(creds.credentials)
    sub = payload.get("sub")
    try:
        user_id = UUID(str(sub))
    except (TypeError, ValueError) as exc:
        raise AppError(401, "UNAUTHORIZED", "Invalid token") from exc
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppError(401, "UNAUTHORIZED", "Invalid token")
    if not user.is_active:
        raise AppError(403, "ACCOUNT_DISABLED", "Account is disabled")
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    def _checker(user: User = Depends(get_current_user)) -> User:
        code = user.role.code if user.role else None
        if code not in roles:
            raise AppError(403, "FORBIDDEN", "You do not have permission to perform this action")
        return user

    return _checker


# Read access for Phase 2 core APIs (geo-scoped in services).
AnyReader = require_roles(
    "ADMIN",
    "ACQUISITION_OFFICER",
    "APPROVING_AUTHORITY",
    "FIELD_OFFICER",
)
ProjectWriter = require_roles("ADMIN", "ACQUISITION_OFFICER")
ProposalWriter = require_roles("ADMIN", "ACQUISITION_OFFICER")
ProposalReader = require_roles("ADMIN", "ACQUISITION_OFFICER", "APPROVING_AUTHORITY")
Approver = require_roles("ADMIN", "APPROVING_AUTHORITY")
OfficerOps = require_roles("ADMIN", "ACQUISITION_OFFICER")
FieldOps = require_roles("ADMIN", "FIELD_OFFICER")
AdminOnly = require_roles("ADMIN")
