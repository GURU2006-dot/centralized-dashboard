from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.acquisition import AcquisitionCase, WorkflowStageDefinition
from app.models.compensation import Compensation
from app.models.family import AffectedFamily, Rehabilitation
from app.models.geo import District, State
from app.models.ml_prediction import MLPrediction
from app.models.project import Project
from app.models.user import User
from app.services.scope import apply_project_scope


class DashboardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _projects(self, user: User, **filters) -> Select:
        stmt = apply_project_scope(select(Project.id), self.db, user)
        stmt = self._apply_filters(stmt, **filters)
        return stmt

    def _apply_filters(
        self,
        stmt: Select,
        *,
        state: str | None = None,
        district: str | None = None,
        project_id=None,
        stage: str | None = None,
        status: str | None = None,
    ) -> Select:
        if state:
            stmt = stmt.where(Project.state_code == state)
        if district:
            stmt = stmt.where(Project.district_code == district)
        if project_id:
            stmt = stmt.where(Project.id == project_id)
        if status:
            stmt = stmt.where(Project.status == status)
        if stage:
            stmt = stmt.where(Project.current_stage == stage)
        return stmt

    def kpis(self, user: User, **filters) -> dict:
        project_ids_sq = self._projects(user, **filters).scalar_subquery()
        total_projects = self.db.scalar(
            select(func.count()).select_from(self._projects(user, **filters).subquery())
        ) or 0
        notified = self.db.scalar(
            select(func.coalesce(func.sum(AcquisitionCase.notified_area_ha), 0)).where(
                AcquisitionCase.project_id.in_(project_ids_sq)
            )
        )
        acquired = self.db.scalar(
            select(func.coalesce(func.sum(AcquisitionCase.acquired_area_ha), 0)).where(
                AcquisitionCase.project_id.in_(project_ids_sq)
            )
        )
        assessed = self.db.scalar(
            select(func.coalesce(func.sum(Compensation.assessed_amount_inr), 0))
            .select_from(Compensation)
            .join(AcquisitionCase, Compensation.acquisition_case_id == AcquisitionCase.id)
            .where(AcquisitionCase.project_id.in_(project_ids_sq))
        )
        paid = self.db.scalar(
            select(func.coalesce(func.sum(Compensation.paid_amount_inr), 0))
            .select_from(Compensation)
            .join(AcquisitionCase, Compensation.acquisition_case_id == AcquisitionCase.id)
            .where(AcquisitionCase.project_id.in_(project_ids_sq))
        )
        families = self.db.scalar(
            select(func.count())
            .select_from(AffectedFamily)
            .where(AffectedFamily.project_id.in_(project_ids_sq))
        ) or 0
        displaced = self.db.scalar(
            select(func.count())
            .select_from(AffectedFamily)
            .where(
                AffectedFamily.project_id.in_(project_ids_sq),
                AffectedFamily.is_displaced.is_(True),
            )
        ) or 0
        rehab_completed = self.db.scalar(
            select(func.count())
            .select_from(Rehabilitation)
            .where(
                Rehabilitation.project_id.in_(project_ids_sq),
                Rehabilitation.status == "COMPLETED",
            )
        ) or 0
        rehab_in_progress = self.db.scalar(
            select(func.count())
            .select_from(Rehabilitation)
            .where(
                Rehabilitation.project_id.in_(project_ids_sq),
                Rehabilitation.status == "IN_PROGRESS",
            )
        ) or 0
        delayed = self.db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.id.in_(project_ids_sq), Project.status == "DELAYED")
        ) or 0
        at_risk = self.db.scalar(
            select(func.count()).select_from(
                select(Project.id)
                .where(Project.id.in_(project_ids_sq))
                .where(
                    (Project.status == "DELAYED")
                    | (
                        Project.id.in_(
                            select(MLPrediction.project_id).where(
                                MLPrediction.risk_level == "HIGH",
                                MLPrediction.project_id.is_not(None),
                            )
                        )
                    )
                )
                .subquery()
            )
        ) or 0
        pct = round((int(rehab_completed) / int(families) * 100), 1) if families else 0.0
        return {
            "total_projects": int(total_projects),
            "area_notified_ha": float(notified or 0),
            "area_acquired_ha": float(acquired or 0),
            "compensation_assessed_inr": float(assessed or 0),
            "compensation_paid_inr": float(paid or 0),
            "affected_families": int(families),
            "displaced_families": int(displaced),
            "rr_progress": {
                "total_families": int(families),
                "rehab_completed": int(rehab_completed),
                "rehab_in_progress": int(rehab_in_progress),
                "pct_complete": pct,
            },
            "projects_at_risk": int(at_risk),
            "delayed_projects": int(delayed),
        }

    def charts(self, user: User, **filters) -> dict:
        project_ids_sq = self._projects(user, **filters).scalar_subquery()
        stages = self.db.execute(
            select(AcquisitionCase.current_stage, func.count())
            .where(AcquisitionCase.project_id.in_(project_ids_sq))
            .group_by(AcquisitionCase.current_stage)
            .order_by(AcquisitionCase.current_stage)
        ).all()
        state_rows = self.db.execute(
            select(
                Project.state_code,
                func.count(func.distinct(Project.id)),
                func.coalesce(func.sum(AcquisitionCase.notified_area_ha), 0),
                func.coalesce(func.sum(AcquisitionCase.acquired_area_ha), 0),
            )
            .select_from(Project)
            .outerjoin(AcquisitionCase, AcquisitionCase.project_id == Project.id)
            .where(Project.id.in_(project_ids_sq))
            .group_by(Project.state_code)
            .order_by(Project.state_code)
        ).all()
        comp_rows = self.db.execute(
            select(
                Project.id,
                Project.code,
                func.coalesce(func.sum(Compensation.assessed_amount_inr), 0),
                func.coalesce(func.sum(Compensation.paid_amount_inr), 0),
            )
            .select_from(Project)
            .join(AcquisitionCase, AcquisitionCase.project_id == Project.id)
            .join(Compensation, Compensation.acquisition_case_id == AcquisitionCase.id)
            .where(Project.id.in_(project_ids_sq))
            .group_by(Project.id, Project.code)
            .order_by(Project.code)
        ).all()
        rr_rows = self.db.execute(
            select(Rehabilitation.status, func.count())
            .where(Rehabilitation.project_id.in_(project_ids_sq))
            .group_by(Rehabilitation.status)
        ).all()
        latest = (
            select(MLPrediction.acquisition_case_id, MLPrediction.risk_level)
            .distinct(MLPrediction.acquisition_case_id)
            .order_by(MLPrediction.acquisition_case_id, MLPrediction.predicted_at.desc())
            .subquery()
        )
        risk_rows = self.db.execute(
            select(latest.c.risk_level, func.count())
            .select_from(latest)
            .join(AcquisitionCase, AcquisitionCase.id == latest.c.acquisition_case_id)
            .where(AcquisitionCase.project_id.in_(project_ids_sq))
            .group_by(latest.c.risk_level)
        ).all()
        return {
            "stage_distribution": [{"stage": s, "count": int(c)} for s, c in stages],
            "state_wise_progress": [
                {
                    "state_code": st,
                    "projects": int(pc),
                    "area_notified_ha": float(n or 0),
                    "area_acquired_ha": float(a or 0),
                }
                for st, pc, n, a in state_rows
            ],
            "compensation": [
                {
                    "project_id": str(pid),
                    "project_code": code,
                    "assessed_inr": float(ass or 0),
                    "paid_inr": float(pd or 0),
                }
                for pid, code, ass, pd in comp_rows
            ],
            "rr_status": [{"status": s, "count": int(c)} for s, c in rr_rows],
            "risk": [{"risk_level": lvl, "count": int(c)} for lvl, c in risk_rows],
        }

    def filters(self, user: User) -> dict:
        project_stmt = apply_project_scope(select(Project), self.db, user)
        projects = self.db.scalars(project_stmt.order_by(Project.code)).all()
        states = self.db.scalars(select(State).order_by(State.code)).all()
        districts = self.db.scalars(select(District).order_by(District.code)).all()
        stages = self.db.scalars(
            select(WorkflowStageDefinition).order_by(WorkflowStageDefinition.sequence_order)
        ).all()
        # Officer/field: only states/districts they can see
        code = user.role.code if user.role else ""
        if code not in ("ADMIN", "APPROVING_AUTHORITY"):
            seen_states = {p.state_code for p in projects}
            seen_districts = {p.district_code for p in projects if p.district_code}
            states = [s for s in states if s.code in seen_states]
            districts = [d for d in districts if d.code in seen_districts]
        return {
            "states": [{"code": s.code, "name": s.name} for s in states],
            "districts": [{"code": d.code, "name": d.name} for d in districts],
            "projects": [{"code": str(p.id), "name": f"{p.code} — {p.name}"} for p in projects],
            "stages": [{"code": s.code, "name": s.name} for s in stages],
            "statuses": [
                {"code": x, "name": x}
                for x in ("PLANNED", "ACTIVE", "DELAYED", "ON_HOLD", "COMPLETED")
            ],
        }
