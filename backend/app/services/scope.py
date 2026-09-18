"""Prototype-level geo / assignment scoping. Not a full policy engine."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.field_verification import FieldVerification
from app.models.parcel import LandParcel
from app.models.project import Project
from app.models.user import User

NATIONAL_ROLES = frozenset({"ADMIN", "APPROVING_AUTHORITY"})


def role_code(user: User) -> str:
    return user.role.code if user.role else ""


def assigned_parcel_ids(db: Session, user: User) -> list[UUID]:
    return list(
        db.scalars(
            select(FieldVerification.parcel_id).where(FieldVerification.assigned_to == user.id)
        ).all()
    )


def assigned_project_ids(db: Session, user: User) -> list[UUID]:
    parcel_ids = assigned_parcel_ids(db, user)
    if not parcel_ids:
        return []
    return list(
        db.scalars(
            select(LandParcel.project_id)
            .where(LandParcel.id.in_(parcel_ids), LandParcel.project_id.is_not(None))
            .distinct()
        ).all()
    )


def apply_project_scope(stmt: Select, db: Session, user: User) -> Select:
    code = role_code(user)
    if code in NATIONAL_ROLES:
        return stmt
    if code == "FIELD_OFFICER":
        ids = assigned_project_ids(db, user)
        return stmt.where(Project.id.in_(ids if ids else [UUID(int=0)]))
    if user.state_code:
        stmt = stmt.where(Project.state_code == user.state_code)
    if user.district_code:
        stmt = stmt.where(Project.district_code == user.district_code)
    return stmt


def apply_parcel_scope(stmt: Select, db: Session, user: User) -> Select:
    code = role_code(user)
    if code in NATIONAL_ROLES:
        return stmt
    if code == "FIELD_OFFICER":
        ids = assigned_parcel_ids(db, user)
        return stmt.where(LandParcel.id.in_(ids if ids else [UUID(int=0)]))
    if user.state_code:
        stmt = stmt.where(LandParcel.state_code == user.state_code)
    if user.district_code:
        stmt = stmt.where(LandParcel.district_code == user.district_code)
    return stmt
