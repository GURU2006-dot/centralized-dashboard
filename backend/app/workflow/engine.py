"""Acquisition-case stage transitions. Not used for proposal approval."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.acquisition import AcquisitionCase, WorkflowEvent
from app.models.compensation import Compensation
from app.models.possession import Possession
from app.models.user import User
from app.repositories.acquisitions import AcquisitionRepository
from app.services.alerts import AlertService
from app.services.audit import AuditService
from app.services.notifications import NotificationService
from app.services.scope import role_code
from app.workflow.stages import is_terminal, next_stage, normalize_stage


class WorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AcquisitionRepository(db)
        self.audit = AuditService(db)
        self.notes = NotificationService(db)
        self.alerts = AlertService(db)

    def transition(self, user: User, case_id: UUID, to_stage: str, remarks: str | None) -> dict:
        code = role_code(user)
        if code == "FIELD_OFFICER":
            raise AppError(403, "FORBIDDEN", "Field officers cannot transition acquisition cases")
        if code == "APPROVING_AUTHORITY":
            raise AppError(
                403,
                "FORBIDDEN",
                "Approving authority acts on proposals only, not case stage transitions",
            )
        if code not in ("ADMIN", "ACQUISITION_OFFICER"):
            raise AppError(403, "FORBIDDEN", "Not permitted to transition cases")

        case = self.repo.get_scoped(user, case_id)
        if case is None:
            raise AppError(404, "NOT_FOUND", "Acquisition case not found")
        if is_terminal(case.current_stage) or case.status == "CLOSED":
            raise AppError(409, "CONFLICT", "Case is already completed")

        target = normalize_stage(to_stage)
        expected = next_stage(case.current_stage)
        if expected is None or target != expected:
            raise AppError(
                400,
                "ILLEGAL_TRANSITION",
                f"Cannot move from {case.current_stage} to {target}. Next stage is {expected}.",
            )
        self._validate_gates(case, target)

        now = datetime.now(timezone.utc)
        from_stage = case.current_stage
        case.current_stage = target
        case.stage_entered_at = now
        case.expected_stage_exit_at = None if target == "COMPLETED" else now + timedelta(days=21)
        if target == "NOTIFICATION" and case.notified_area_ha is None and case.parcel is not None:
            case.notified_area_ha = case.parcel.area_ha
        if target in ("POSSESSION", "REHABILITATION_RESETTLEMENT", "COMPLETED") and case.parcel:
            case.acquired_area_ha = case.parcel.area_ha
        if target == "COMPLETED":
            case.status = "CLOSED"
            case.completed_at = now
            if case.parcel:
                case.parcel.acquisition_status = "ACQUIRED"
                case.parcel.current_stage = target
        elif case.parcel:
            case.parcel.current_stage = target
            if case.parcel.acquisition_status == "NOT_STARTED":
                case.parcel.acquisition_status = "IN_PROCESS"

        self.db.add(
            WorkflowEvent(
                id=uuid4(),
                acquisition_case_id=case.id,
                from_stage=from_stage,
                to_stage=target,
                occurred_at=now,
                actor_user_id=user.id,
                remarks=remarks,
                extra_metadata={"source": "transition"},
            )
        )
        self.audit.record(
            user,
            "WORKFLOW_STAGE_CHANGED",
            "acquisition_case",
            case.id,
            {"from_stage": from_stage, "to_stage": target, "remarks": remarks},
        )
        self.notes.notify_roles(
            ["ACQUISITION_OFFICER", "ADMIN"],
            "Workflow transitioned",
            f"Case {case.case_number}: {from_stage} → {target}",
            "acquisition_case",
            str(case.id),
            exclude_user_id=user.id,
        )
        self.alerts.evaluate(project_id=case.project_id)
        self.db.commit()
        from app.services.acquisitions import AcquisitionService

        return AcquisitionService(self.db).get(user, case.id)

    def _validate_gates(self, case: AcquisitionCase, target: str) -> None:
        if target == "COMPENSATION_PAID":
            comp = self.db.scalars(
                select(Compensation).where(Compensation.acquisition_case_id == case.id)
            ).first()
            if (
                comp is None
                or not comp.assessed_amount_inr
                or float(comp.assessed_amount_inr) <= 0
                or float(comp.paid_amount_inr or 0) < float(comp.assessed_amount_inr)
            ):
                raise AppError(
                    400,
                    "VALIDATION_ERROR",
                    "Compensation must be assessed and fully paid before COMPENSATION_PAID",
                )
        if target == "COMPLETED":
            poss = self.db.scalars(
                select(Possession).where(Possession.acquisition_case_id == case.id)
            ).first()
            if poss is None or poss.status != "TAKEN":
                raise AppError(
                    400,
                    "VALIDATION_ERROR",
                    "Possession must be TAKEN before the case can be COMPLETED",
                )
