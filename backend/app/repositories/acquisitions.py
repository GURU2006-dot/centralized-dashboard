from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.models.acquisition import AcquisitionCase, WorkflowEvent, WorkflowStageDefinition
from app.models.compensation import Compensation
from app.models.family import AffectedFamily, Rehabilitation, Resettlement
from app.models.ml_prediction import MLPrediction
from app.models.parcel import LandParcel
from app.models.possession import Possession
from app.models.project import Project
from app.models.user import User
from app.services.scope import apply_parcel_scope, apply_project_scope


class AcquisitionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _latest_risk(self):
        return (
            select(
                MLPrediction.acquisition_case_id,
                MLPrediction.risk_level,
                MLPrediction.risk_score,
            )
            .distinct(MLPrediction.acquisition_case_id)
            .order_by(MLPrediction.acquisition_case_id, MLPrediction.predicted_at.desc())
            .subquery()
        )

    def _base(self, user: User) -> Select:
        stmt = select(AcquisitionCase).join(Project, AcquisitionCase.project_id == Project.id)
        stmt = apply_project_scope(stmt, self.db, user)
        # Field officers are also constrained to assigned parcels.
        if user.role and user.role.code == "FIELD_OFFICER":
            stmt = stmt.join(LandParcel, AcquisitionCase.parcel_id == LandParcel.id)
            stmt = apply_parcel_scope(stmt, self.db, user)
        return stmt

    def list_filtered(
        self,
        user: User,
        *,
        project_id: UUID | None,
        parcel_id: UUID | None,
        state: str | None,
        district: str | None,
        stage: str | None,
        status: str | None,
        risk_level: str | None = None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple], int]:
        risk = self._latest_risk()
        stmt = (
            select(AcquisitionCase, Project, LandParcel, risk.c.risk_level, risk.c.risk_score)
            .join(Project, AcquisitionCase.project_id == Project.id)
            .join(LandParcel, AcquisitionCase.parcel_id == LandParcel.id)
            .outerjoin(risk, risk.c.acquisition_case_id == AcquisitionCase.id)
        )
        stmt = apply_project_scope(stmt, self.db, user)
        if user.role and user.role.code == "FIELD_OFFICER":
            stmt = apply_parcel_scope(stmt, self.db, user)
        if project_id:
            stmt = stmt.where(AcquisitionCase.project_id == project_id)
        if parcel_id:
            stmt = stmt.where(AcquisitionCase.parcel_id == parcel_id)
        if state:
            stmt = stmt.where(Project.state_code == state)
        if district:
            stmt = stmt.where(Project.district_code == district)
        if stage:
            stmt = stmt.where(AcquisitionCase.current_stage == stage)
        if status:
            stmt = stmt.where(AcquisitionCase.status == status)
        if risk_level:
            stmt = stmt.where(risk.c.risk_level == risk_level)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.db.execute(
            stmt.order_by(AcquisitionCase.case_number)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(rows), int(total)

    def get_scoped(self, user: User, case_id: UUID) -> AcquisitionCase | None:
        stmt = (
            self._base(user)
            .options(
                selectinload(AcquisitionCase.project),
                selectinload(AcquisitionCase.parcel),
            )
            .where(AcquisitionCase.id == case_id)
        )
        return self.db.scalars(stmt).unique().first()

    def compensation(self, case_id: UUID) -> Compensation | None:
        return self.db.scalars(
            select(Compensation).where(Compensation.acquisition_case_id == case_id)
        ).first()

    def possession(self, case_id: UUID) -> Possession | None:
        return self.db.scalars(
            select(Possession).where(Possession.acquisition_case_id == case_id)
        ).first()

    def rr_for_project(self, project_id: UUID) -> dict:
        families = self.db.scalar(
            select(func.count()).select_from(AffectedFamily).where(
                AffectedFamily.project_id == project_id
            )
        ) or 0
        displaced = self.db.scalar(
            select(func.count())
            .select_from(AffectedFamily)
            .where(AffectedFamily.project_id == project_id, AffectedFamily.is_displaced.is_(True))
        ) or 0
        rehab_done = self.db.scalar(
            select(func.count())
            .select_from(Rehabilitation)
            .where(Rehabilitation.project_id == project_id, Rehabilitation.status == "COMPLETED")
        ) or 0
        resettled = self.db.scalar(
            select(func.count())
            .select_from(Resettlement)
            .where(Resettlement.project_id == project_id, Resettlement.status == "POSSESSED")
        ) or 0
        return {
            "affected_families": int(families),
            "displaced_families": int(displaced),
            "rehab_completed": int(rehab_done),
            "resettled": int(resettled),
        }

    def latest_risk(self, case_id: UUID) -> tuple[str, float] | None:
        row = self.db.execute(
            select(MLPrediction.risk_level, MLPrediction.risk_score)
            .where(MLPrediction.acquisition_case_id == case_id)
            .order_by(MLPrediction.predicted_at.desc())
            .limit(1)
        ).first()
        if not row:
            return None
        return str(row[0]), float(row[1])

    def timeline(self, case_id: UUID) -> list[tuple[WorkflowEvent, User | None]]:
        Actor = aliased(User)
        rows = self.db.execute(
            select(WorkflowEvent, Actor)
            .outerjoin(Actor, WorkflowEvent.actor_user_id == Actor.id)
            .where(WorkflowEvent.acquisition_case_id == case_id)
            .order_by(WorkflowEvent.occurred_at.asc())
        ).all()
        return list(rows)

    def stage_codes(self) -> list[str]:
        return list(
            self.db.scalars(
                select(WorkflowStageDefinition.code).order_by(
                    WorkflowStageDefinition.sequence_order
                )
            ).all()
        )
