from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.schemas.common import envelope
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    data = AuthService(db).login(body.email, body.password)
    return envelope(data)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return envelope(AuthService.to_public(user))
