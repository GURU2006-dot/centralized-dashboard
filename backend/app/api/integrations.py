from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AdminOnly, AnyReader, OfficerOps
from app.models.user import User
from app.schemas.common import envelope
from app.services.integrations import IntegrationService

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class LookupBody(BaseModel):
    ulpin: str


@router.get("/status")
def status(user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(IntegrationService(db).status())


@router.post("/{system}/lookup")
def lookup(
    system: str,
    body: LookupBody,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(IntegrationService(db).lookup(user, system, body.ulpin))


@router.post("/{system}/sync")
def sync(system: str, user: User = Depends(AdminOnly), db: Session = Depends(get_db)):
    return envelope(IntegrationService(db).sync(user, system))
