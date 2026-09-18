from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.acquisition import AcquisitionCase
from app.models.compensation import Compensation
from app.models.family import AffectedFamily
from app.models.parcel import LandParcel
from app.models.project import Project
from app.models.user import User
from app.services.scope import apply_project_scope


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _base(self, user: User) -> Select:
        return apply_project_scope(select(Project), self.db, user)

    def list_filtered(
        self,
        user: User,
        *,
        search: str | None,
        state: str | None,
        district: str | None,
        status: str | None,
        stage: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Project], int]:
        stmt = self._base(user)
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(Project.name.ilike(q), Project.code.ilike(q), Project.purpose.ilike(q))
            )
        if state:
            stmt = stmt.where(Project.state_code == state)
        if district:
            stmt = stmt.where(Project.district_code == district)
        if status:
            stmt = stmt.where(Project.status == status)
        if stage:
            stmt = stmt.where(Project.current_stage == stage)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(Project.code).offset((page - 1) * page_size).limit(page_size)
            ).all()
        )
        return rows, int(total)

    def get_scoped(self, user: User, project_id: UUID) -> Project | None:
        stmt = self._base(user).where(Project.id == project_id)
        return self.db.scalars(stmt).first()

    def get_by_code(self, code: str) -> Project | None:
        return self.db.scalars(select(Project).where(Project.code == code)).first()

    def add(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        return project

    def summaries(self, project_id: UUID) -> dict:
        parcel_count = self.db.scalar(
            select(func.count()).select_from(LandParcel).where(LandParcel.project_id == project_id)
        ) or 0
        case_count = self.db.scalar(
            select(func.count())
            .select_from(AcquisitionCase)
            .where(AcquisitionCase.project_id == project_id)
        ) or 0
        notified = self.db.scalar(
            select(func.coalesce(func.sum(AcquisitionCase.notified_area_ha), 0)).where(
                AcquisitionCase.project_id == project_id
            )
        )
        acquired = self.db.scalar(
            select(func.coalesce(func.sum(AcquisitionCase.acquired_area_ha), 0)).where(
                AcquisitionCase.project_id == project_id
            )
        )
        assessed = self.db.scalar(
            select(func.coalesce(func.sum(Compensation.assessed_amount_inr), 0))
            .select_from(Compensation)
            .join(AcquisitionCase, Compensation.acquisition_case_id == AcquisitionCase.id)
            .where(AcquisitionCase.project_id == project_id)
        )
        paid = self.db.scalar(
            select(func.coalesce(func.sum(Compensation.paid_amount_inr), 0))
            .select_from(Compensation)
            .join(AcquisitionCase, Compensation.acquisition_case_id == AcquisitionCase.id)
            .where(AcquisitionCase.project_id == project_id)
        )
        families = self.db.scalar(
            select(func.count())
            .select_from(AffectedFamily)
            .where(AffectedFamily.project_id == project_id)
        ) or 0
        displaced = self.db.scalar(
            select(func.count())
            .select_from(AffectedFamily)
            .where(AffectedFamily.project_id == project_id, AffectedFamily.is_displaced.is_(True))
        ) or 0
        return {
            "parcel_count": int(parcel_count),
            "case_count": int(case_count),
            "area_notified_ha": float(notified or 0),
            "area_acquired_ha": float(acquired or 0),
            "compensation_assessed_inr": float(assessed or 0),
            "compensation_paid_inr": float(paid or 0),
            "affected_families": int(families),
            "displaced_families": int(displaced),
        }
