from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.alert import Alert
from app.models.acquisition import AcquisitionCase
from app.models.compensation import Compensation
from app.models.field_verification import FieldVerification
from app.models.ml_prediction import MLPrediction
from app.models.project import Project
from app.models.proposal import Proposal
from app.models.user import User
from app.repositories.users import UserRepository


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _exists_open(
        self,
        rule_code: str,
        recipient_id: UUID,
        *,
        case_id: UUID | None = None,
        project_id: UUID | None = None,
        parcel_id: UUID | None = None,
        extra_key: str | None = None,
    ) -> bool:
        stmt = select(Alert.id).where(
            Alert.rule_code == rule_code,
            Alert.recipient_user_id == recipient_id,
            Alert.is_read.is_(False),
        )
        if case_id:
            stmt = stmt.where(Alert.acquisition_case_id == case_id)
        if project_id:
            stmt = stmt.where(Alert.project_id == project_id)
        if parcel_id:
            stmt = stmt.where(Alert.parcel_id == parcel_id)
        if extra_key:
            stmt = stmt.where(Alert.message.contains(extra_key))
        return self.db.scalars(stmt.limit(1)).first() is not None

    def _emit(
        self,
        *,
        rule_code: str,
        alert_type: str,
        severity: str,
        message: str,
        recipient_id: UUID,
        project_id: UUID | None = None,
        parcel_id: UUID | None = None,
        case_id: UUID | None = None,
        extra_key: str | None = None,
    ) -> bool:
        if self._exists_open(
            rule_code,
            recipient_id,
            case_id=case_id,
            project_id=project_id,
            parcel_id=parcel_id,
            extra_key=extra_key,
        ):
            return False
        self.db.add(
            Alert(
                id=uuid4(),
                rule_code=rule_code,
                alert_type=alert_type,
                severity=severity,
                project_id=project_id,
                parcel_id=parcel_id,
                acquisition_case_id=case_id,
                message=message,
                recipient_user_id=recipient_id,
                is_read=False,
                extra_metadata={"synthetic": True},
                data_source="SYNTHETIC",
            )
        )
        return True

    def _officer_ids(self) -> list[UUID]:
        repo = UserRepository(self.db)
        return [u.id for u in repo.list_by_role("ACQUISITION_OFFICER")] + [
            u.id for u in repo.list_by_role("ADMIN")
        ]

    def _approver_ids(self) -> list[UUID]:
        repo = UserRepository(self.db)
        return [u.id for u in repo.list_by_role("APPROVING_AUTHORITY")] + [
            u.id for u in repo.list_by_role("ADMIN")
        ]

    def evaluate(self, *, project_id: UUID | None = None) -> int:
        created = 0
        now = datetime.now(timezone.utc)
        officers = self._officer_ids()
        approvers = self._approver_ids()

        pending = self.db.scalars(
            select(Proposal).where(Proposal.status == "UNDER_VERIFICATION")
        ).all()
        for prop in pending:
            key = str(prop.id)
            msg = f"Proposal {prop.proposal_number} awaiting approval ({key})"
            for rid in approvers:
                if self._emit(
                    rule_code="APPROVAL_PENDING",
                    alert_type="PROPOSAL",
                    severity="MEDIUM",
                    message=msg,
                    recipient_id=rid,
                    project_id=prop.project_id,
                    extra_key=key,
                ):
                    created += 1

        stmt = select(AcquisitionCase)
        if project_id:
            stmt = stmt.where(AcquisitionCase.project_id == project_id)
        cases = self.db.scalars(stmt).all()
        for case in cases:
            if (
                case.expected_stage_exit_at
                and case.expected_stage_exit_at < now
                and case.status == "OPEN"
            ):
                msg = f"Case {case.case_number} stage {case.current_stage} overrun"
                for rid in officers:
                    if self._emit(
                        rule_code="STAGE_OVERRUN",
                        alert_type="DELAY",
                        severity="HIGH",
                        message=msg,
                        recipient_id=rid,
                        project_id=case.project_id,
                        parcel_id=case.parcel_id,
                        case_id=case.id,
                    ):
                        created += 1
            if case.current_stage == "POSSESSION":
                msg = f"Case {case.case_number} possession pending"
                for rid in officers:
                    if self._emit(
                        rule_code="POSSESSION_PENDING",
                        alert_type="POSSESSION",
                        severity="MEDIUM",
                        message=msg,
                        recipient_id=rid,
                        project_id=case.project_id,
                        case_id=case.id,
                    ):
                        created += 1
            if case.current_stage == "REHABILITATION_RESETTLEMENT":
                msg = f"Case {case.case_number} R&R pending"
                for rid in officers:
                    if self._emit(
                        rule_code="RR_PENDING",
                        alert_type="RR",
                        severity="MEDIUM",
                        message=msg,
                        recipient_id=rid,
                        project_id=case.project_id,
                        case_id=case.id,
                    ):
                        created += 1

        comps = self.db.scalars(select(Compensation)).all()
        for comp in comps:
            if (
                comp.due_date
                and comp.status not in ("PAID",)
                and comp.due_date < now.date()
            ):
                msg = f"Compensation overdue for case {comp.acquisition_case_id}"
                for rid in officers:
                    if self._emit(
                        rule_code="COMPENSATION_DUE",
                        alert_type="COMPENSATION",
                        severity="HIGH",
                        message=msg,
                        recipient_id=rid,
                        case_id=comp.acquisition_case_id,
                    ):
                        created += 1

        delayed = self.db.scalars(select(Project).where(Project.status == "DELAYED")).all()
        for proj in delayed:
            msg = f"Project {proj.code} marked DELAYED"
            for rid in officers:
                if self._emit(
                    rule_code="PROJECT_DELAYED",
                    alert_type="DELAY",
                    severity="HIGH",
                    message=msg,
                    recipient_id=rid,
                    project_id=proj.id,
                ):
                    created += 1

        fields = self.db.scalars(
            select(FieldVerification).where(
                FieldVerification.status.in_(("ASSIGNED", "IN_PROGRESS"))
            )
        ).all()
        for fv in fields:
            msg = f"Field verification incomplete ({fv.id})"
            if self._emit(
                rule_code="FIELD_INCOMPLETE",
                alert_type="FIELD",
                severity="LOW",
                message=msg,
                recipient_id=fv.assigned_to,
                parcel_id=fv.parcel_id,
                case_id=fv.acquisition_case_id,
                extra_key=str(fv.id),
            ):
                created += 1

        highs = self.db.scalars(
            select(MLPrediction).where(MLPrediction.risk_level == "HIGH")
        ).all()
        seen_cases: set[UUID] = set()
        for pred in highs:
            if pred.acquisition_case_id in seen_cases:
                continue
            seen_cases.add(pred.acquisition_case_id)
            msg = f"High model risk score on case {pred.acquisition_case_id}"
            for rid in officers:
                if self._emit(
                    rule_code="ML_HIGH_RISK",
                    alert_type="ML",
                    severity="HIGH",
                    message=msg,
                    recipient_id=rid,
                    project_id=pred.project_id,
                    case_id=pred.acquisition_case_id,
                ):
                    created += 1
        return created

    def emit_ml_high(self, case: AcquisitionCase, *, score_100: float) -> int:
        created = 0
        msg = (
            f"HIGH DELAY RISK: Acquisition case {case.case_number} has a delay risk score "
            f"of {score_100}/100."
        )
        for rid in self._officer_ids():
            if self._emit(
                rule_code="ML_HIGH_RISK",
                alert_type="ML",
                severity="HIGH",
                message=msg,
                recipient_id=rid,
                project_id=case.project_id,
                parcel_id=case.parcel_id,
                case_id=case.id,
            ):
                created += 1
        return created

    def list_for(self, user: User, *, unread: bool | None, page: int, page_size: int):
        stmt = select(Alert)
        if user.role and user.role.code != "ADMIN":
            stmt = stmt.where(Alert.recipient_user_id == user.id)
        if unread:
            stmt = stmt.where(Alert.is_read.is_(False))
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(Alert.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return rows, int(total)

    def mark_read(self, user: User, alert_id: UUID) -> Alert:
        row = self.db.get(Alert, alert_id)
        if row is None:
            raise AppError(404, "NOT_FOUND", "Alert not found")
        if user.role and user.role.code != "ADMIN" and row.recipient_user_id != user.id:
            raise AppError(403, "FORBIDDEN", "You cannot update this alert")
        row.is_read = True
        return row
