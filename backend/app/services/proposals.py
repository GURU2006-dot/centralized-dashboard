from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.errors import AppError
from app.models.acquisition import AcquisitionCase, WorkflowEvent
from app.models.parcel import LandParcel
from app.models.project import Project
from app.models.proposal import Proposal, ProposalParcel
from app.models.user import User
from app.schemas.common import as_float
from app.services.alerts import AlertService
from app.services.audit import AuditService
from app.services.notifications import NotificationService
from app.services.scope import apply_project_scope
from app.workflow.stages import INITIAL_STAGE

ALLOWED = {
    "DRAFT": {"SUBMITTED"},
    "SUBMITTED": {"UNDER_VERIFICATION"},
    "UNDER_VERIFICATION": {"APPROVED", "REJECTED"},
}


def _serialize(proposal: Proposal) -> dict:
    return {
        "id": proposal.id,
        "proposal_number": proposal.proposal_number,
        "project_id": proposal.project_id,
        "project_code": proposal.project.code if proposal.project else None,
        "required_area_ha": as_float(proposal.required_area_ha),
        "purpose": proposal.purpose,
        "estimated_compensation_inr": as_float(proposal.estimated_compensation_inr),
        "affected_families_count": proposal.affected_families_count,
        "proposed_start": proposal.proposed_start,
        "proposed_end": proposal.proposed_end,
        "status": proposal.status,
        "parcel_ids": [link.parcel_id for link in proposal.parcels],
        "submitted_by": proposal.submitted_by,
        "submitted_at": proposal.submitted_at,
        "reviewed_by": proposal.reviewed_by,
        "reviewed_at": proposal.reviewed_at,
        "review_remarks": proposal.review_remarks,
        "data_source": proposal.data_source,
    }


class ProposalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.notes = NotificationService(db)
        self.alerts = AlertService(db)

    def _scoped_stmt(self, user: User):
        stmt = (
            select(Proposal)
            .join(Project, Proposal.project_id == Project.id)
            .options(
                selectinload(Proposal.project),
                selectinload(Proposal.parcels),
            )
        )
        return apply_project_scope(stmt, self.db, user)

    def _get(self, user: User, proposal_id: UUID) -> Proposal:
        row = self.db.scalars(self._scoped_stmt(user).where(Proposal.id == proposal_id)).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Proposal not found")
        return row

    def _next_number(self) -> str:
        n = (self.db.scalar(select(func.count()).select_from(Proposal)) or 0) + 1
        return f"PROP-2026-{n:04d}-{uuid4().hex[:6].upper()}"

    def list_proposals(self, user: User, *, status: str | None, project_id: UUID | None, page: int, page_size: int):
        stmt = self._scoped_stmt(user)
        if status:
            stmt = stmt.where(Proposal.status == status)
        if project_id:
            stmt = stmt.where(Proposal.project_id == project_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(Proposal.proposal_number)
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).unique()
            .all()
        )
        return [_serialize(p) for p in rows], int(total)

    def get(self, user: User, proposal_id: UUID) -> dict:
        return _serialize(self._get(user, proposal_id))

    def create(self, user: User, body) -> dict:
        project = self.db.scalars(
            apply_project_scope(select(Project), self.db, user).where(Project.id == body.project_id)
        ).first()
        if project is None:
            raise AppError(404, "NOT_FOUND", "Project not found")
        parcel_ids = list(body.parcel_ids or [])
        if parcel_ids:
            found = list(
                self.db.scalars(
                    select(LandParcel).where(
                        LandParcel.id.in_(parcel_ids), LandParcel.project_id == project.id
                    )
                ).all()
            )
            if len(found) != len(set(parcel_ids)):
                raise AppError(400, "VALIDATION_ERROR", "One or more parcels do not belong to the project")
        proposal = Proposal(
            id=uuid4(),
            proposal_number=body.proposal_number or self._next_number(),
            project_id=project.id,
            required_area_ha=body.required_area_ha,
            purpose=body.purpose,
            estimated_compensation_inr=body.estimated_compensation_inr,
            affected_families_count=body.affected_families_count,
            proposed_start=body.proposed_start,
            proposed_end=body.proposed_end,
            status="DRAFT",
            data_source="SYNTHETIC",
        )
        self.db.add(proposal)
        self.db.flush()
        for pid in parcel_ids:
            self.db.add(ProposalParcel(proposal_id=proposal.id, parcel_id=pid))
        self.audit.record(user, "PROPOSAL_CREATED", "proposal", proposal.id, {"number": proposal.proposal_number})
        self.db.commit()
        return self.get(user, proposal.id)

    def update(self, user: User, proposal_id: UUID, body) -> dict:
        proposal = self._get(user, proposal_id)
        if proposal.status != "DRAFT":
            raise AppError(409, "CONFLICT", "Only DRAFT proposals can be edited")
        data = body.model_dump(exclude_unset=True)
        parcel_ids = data.pop("parcel_ids", None)
        for key, value in data.items():
            setattr(proposal, key, value)
        if parcel_ids is not None:
            from sqlalchemy import delete

            self.db.execute(delete(ProposalParcel).where(ProposalParcel.proposal_id == proposal.id))
            for pid in parcel_ids:
                parcel = self.db.get(LandParcel, pid)
                if parcel is None or parcel.project_id != proposal.project_id:
                    raise AppError(400, "VALIDATION_ERROR", "Parcel does not belong to the project")
                self.db.add(ProposalParcel(proposal_id=proposal.id, parcel_id=pid))
        self.db.commit()
        return self.get(user, proposal.id)

    def _transition(self, proposal: Proposal, to_status: str) -> None:
        allowed = ALLOWED.get(proposal.status, set())
        if to_status not in allowed:
            raise AppError(
                400,
                "ILLEGAL_TRANSITION",
                f"Cannot move proposal from {proposal.status} to {to_status}",
            )

    def submit(self, user: User, proposal_id: UUID, remarks: str | None) -> dict:
        proposal = self._get(user, proposal_id)
        if proposal.status != "DRAFT":
            raise AppError(409, "CONFLICT", "Proposal is not in DRAFT")
        if not proposal.purpose or proposal.required_area_ha is None:
            raise AppError(400, "VALIDATION_ERROR", "Purpose and required area are required")
        if not proposal.parcels:
            raise AppError(400, "VALIDATION_ERROR", "At least one parcel is required")
        self._transition(proposal, "SUBMITTED")
        now = datetime.now(timezone.utc)
        proposal.status = "SUBMITTED"
        proposal.submitted_by = user.id
        proposal.submitted_at = now
        self.audit.record(user, "PROPOSAL_SUBMITTED", "proposal", proposal.id, {"remarks": remarks})
        self.notes.notify_roles(
            ["APPROVING_AUTHORITY", "ADMIN"],
            "Proposal submitted",
            f"{proposal.proposal_number} was submitted and needs verification/approval.",
            "proposal",
            str(proposal.id),
            exclude_user_id=user.id,
        )
        self.db.commit()
        return self.get(user, proposal.id)

    def verify(self, user: User, proposal_id: UUID, remarks: str | None) -> dict:
        proposal = self._get(user, proposal_id)
        if proposal.status != "SUBMITTED":
            raise AppError(409, "CONFLICT", "Proposal is not SUBMITTED")
        self._transition(proposal, "UNDER_VERIFICATION")
        proposal.status = "UNDER_VERIFICATION"
        proposal.review_remarks = remarks
        self.audit.record(user, "PROPOSAL_VERIFIED", "proposal", proposal.id, {"remarks": remarks})
        self.notes.notify_roles(
            ["APPROVING_AUTHORITY", "ADMIN"],
            "Approval required",
            f"{proposal.proposal_number} is under verification and ready for approval.",
            "proposal",
            str(proposal.id),
        )
        self.alerts.evaluate(project_id=proposal.project_id)
        self.db.commit()
        return self.get(user, proposal.id)

    def approve(self, user: User, proposal_id: UUID, remarks: str | None) -> dict:
        proposal = self._get(user, proposal_id)
        if proposal.status == "APPROVED":
            raise AppError(409, "CONFLICT", "Proposal is already approved")
        if proposal.status != "UNDER_VERIFICATION":
            raise AppError(409, "CONFLICT", "Proposal must be UNDER_VERIFICATION to approve")
        self._transition(proposal, "APPROVED")
        now = datetime.now(timezone.utc)
        proposal.status = "APPROVED"
        proposal.reviewed_by = user.id
        proposal.reviewed_at = now
        proposal.review_remarks = remarks or proposal.review_remarks
        created = 0
        existing = 0
        for link in proposal.parcels:
            found = self.db.scalars(
                select(AcquisitionCase).where(
                    AcquisitionCase.project_id == proposal.project_id,
                    AcquisitionCase.parcel_id == link.parcel_id,
                )
            ).first()
            if found:
                existing += 1
                if found.proposal_id is None:
                    found.proposal_id = proposal.id
                continue
            parcel = self.db.get(LandParcel, link.parcel_id)
            n = (self.db.scalar(select(func.count()).select_from(AcquisitionCase)) or 0) + 1
            case = AcquisitionCase(
                id=uuid4(),
                case_number=f"ACQ-2026-{n:04d}-{uuid4().hex[:4].upper()}",
                project_id=proposal.project_id,
                parcel_id=link.parcel_id,
                proposal_id=proposal.id,
                current_stage=INITIAL_STAGE,
                status="OPEN",
                notified_area_ha=None,
                acquired_area_ha=None,
                stage_entered_at=now,
                expected_stage_exit_at=now + timedelta(days=60),
                started_at=now,
                data_source="SYNTHETIC",
            )
            self.db.add(case)
            self.db.flush()
            self.db.add(
                WorkflowEvent(
                    id=uuid4(),
                    acquisition_case_id=case.id,
                    from_stage=None,
                    to_stage=INITIAL_STAGE,
                    occurred_at=now,
                    actor_user_id=user.id,
                    remarks="Case opened after proposal approval",
                    extra_metadata={"source": "proposal_approval", "proposal_id": str(proposal.id)},
                )
            )
            if parcel:
                parcel.acquisition_status = "IN_PROCESS"
                parcel.current_stage = INITIAL_STAGE
            created += 1
        self.audit.record(
            user,
            "PROPOSAL_APPROVED",
            "proposal",
            proposal.id,
            {"cases_created": created, "cases_existing": existing, "remarks": remarks},
        )
        if proposal.submitted_by:
            self.notes.notify(
                proposal.submitted_by,
                "Proposal approved",
                f"{proposal.proposal_number} was approved. {created} acquisition case(s) opened.",
                "proposal",
                str(proposal.id),
            )
        self.db.commit()
        data = self.get(user, proposal.id)
        data["cases_created"] = created
        data["cases_already_present"] = existing
        return data

    def reject(self, user: User, proposal_id: UUID, remarks: str) -> dict:
        if not remarks or not remarks.strip():
            raise AppError(400, "VALIDATION_ERROR", "Rejection remarks are required")
        proposal = self._get(user, proposal_id)
        if proposal.status == "REJECTED":
            raise AppError(409, "CONFLICT", "Proposal is already rejected")
        if proposal.status != "UNDER_VERIFICATION":
            raise AppError(409, "CONFLICT", "Proposal must be UNDER_VERIFICATION to reject")
        self._transition(proposal, "REJECTED")
        proposal.status = "REJECTED"
        proposal.reviewed_by = user.id
        proposal.reviewed_at = datetime.now(timezone.utc)
        proposal.review_remarks = remarks.strip()
        self.audit.record(user, "PROPOSAL_REJECTED", "proposal", proposal.id, {"remarks": remarks})
        if proposal.submitted_by:
            self.notes.notify(
                proposal.submitted_by,
                "Proposal rejected",
                f"{proposal.proposal_number} was rejected: {remarks.strip()}",
                "proposal",
                str(proposal.id),
            )
        self.db.commit()
        return self.get(user, proposal.id)
