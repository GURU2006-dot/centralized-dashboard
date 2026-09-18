from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.family import AffectedFamily
from app.models.project import Project
from app.models.user import User
from app.services.audit import AuditService
from app.services.scope import apply_project_scope


class FamilyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def _stmt(self, user: User):
        stmt = select(AffectedFamily).join(Project, AffectedFamily.project_id == Project.id)
        return apply_project_scope(stmt, self.db, user)

    def list_families(self, user: User, *, project_id: UUID | None, page: int, page_size: int):
        stmt = self._stmt(user)
        if project_id:
            stmt = stmt.where(AffectedFamily.project_id == project_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(stmt.order_by(AffectedFamily.family_head_name).offset((page - 1) * page_size).limit(page_size)).all()
        )
        return [self._ser(r) for r in rows], int(total)

    def get(self, user: User, family_id: UUID) -> dict:
        row = self.db.scalars(self._stmt(user).where(AffectedFamily.id == family_id)).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Family not found")
        return self._ser(row)

    def create(self, user: User, body) -> dict:
        project = self.db.scalars(
            apply_project_scope(select(Project), self.db, user).where(Project.id == body.project_id)
        ).first()
        if project is None:
            raise AppError(404, "NOT_FOUND", "Project not found")
        row = AffectedFamily(
            id=uuid4(),
            project_id=body.project_id,
            parcel_id=body.parcel_id,
            family_head_name=body.family_head_name,
            member_count=body.member_count,
            is_displaced=body.is_displaced,
            contact=None,
            status=body.status or "IDENTIFIED",
            data_source="SYNTHETIC",
        )
        self.db.add(row)
        self.audit.record(user, "FAMILY_CREATED", "affected_family", row.id)
        self.db.commit()
        return self._ser(row)

    def update(self, user: User, family_id: UUID, body) -> dict:
        row = self.db.scalars(self._stmt(user).where(AffectedFamily.id == family_id)).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Family not found")
        data = body.model_dump(exclude_unset=True)
        data.pop("contact", None)
        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        self.audit.record(user, "FAMILY_UPDATED", "affected_family", row.id)
        self.db.commit()
        return self._ser(row)

    @staticmethod
    def _ser(row: AffectedFamily) -> dict:
        return {
            "id": row.id,
            "project_id": row.project_id,
            "parcel_id": row.parcel_id,
            "family_head_name": row.family_head_name,
            "member_count": row.member_count,
            "is_displaced": row.is_displaced,
            "status": row.status,
            "data_source": row.data_source,
        }
