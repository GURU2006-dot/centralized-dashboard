from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.compensation import Compensation
from app.models.user import User
from app.repositories.acquisitions import AcquisitionRepository
from app.schemas.common import as_float
from app.services.audit import AuditService
from app.services.notifications import NotificationService


def _serialize(row: Compensation) -> dict:
    assessed = as_float(row.assessed_amount_inr) or 0.0
    paid = as_float(row.paid_amount_inr) or 0.0
    return {
        "id": row.id,
        "acquisition_case_id": row.acquisition_case_id,
        "assessed_amount_inr": assessed,
        "paid_amount_inr": paid,
        "remaining_amount_inr": round(max(assessed - paid, 0.0), 2),
        "assessment_date": row.assessment_date,
        "payment_date": row.payment_date,
        "due_date": row.due_date,
        "status": row.status,
        "remarks": row.remarks,
        "data_source": row.data_source,
    }


def _status(assessed: float, paid: float) -> str:
    if assessed <= 0:
        return "NOT_ASSESSED"
    if paid <= 0:
        return "ASSESSED"
    if paid < assessed:
        return "PARTIAL"
    return "PAID"


class CompensationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cases = AcquisitionRepository(db)
        self.audit = AuditService(db)
        self.notes = NotificationService(db)

    def _case(self, user: User, case_id: UUID):
        case = self.cases.get_scoped(user, case_id)
        if case is None:
            raise AppError(404, "NOT_FOUND", "Acquisition case not found")
        return case

    def get(self, user: User, case_id: UUID) -> dict:
        self._case(user, case_id)
        row = self.db.scalars(
            select(Compensation).where(Compensation.acquisition_case_id == case_id)
        ).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Compensation record not found")
        return _serialize(row)

    def create(self, user: User, body) -> dict:
        case = self._case(user, body.acquisition_case_id)
        existing = self.db.scalars(
            select(Compensation).where(Compensation.acquisition_case_id == case.id)
        ).first()
        if existing:
            raise AppError(409, "CONFLICT", "Compensation already exists for this case")
        assessed = float(body.assessed_amount_inr or 0)
        paid = float(body.paid_amount_inr or 0)
        if assessed < 0 or paid < 0:
            raise AppError(400, "VALIDATION_ERROR", "Amounts must be >= 0")
        if paid > assessed:
            raise AppError(400, "VALIDATION_ERROR", "paid_amount cannot exceed assessed_amount")
        row = Compensation(
            id=uuid4(),
            acquisition_case_id=case.id,
            assessed_amount_inr=assessed,
            paid_amount_inr=paid,
            status=_status(assessed, paid),
            assessment_date=body.assessment_date,
            due_date=body.due_date,
            payment_date=body.payment_date,
            remarks=body.remarks,
            data_source="SYNTHETIC",
        )
        self.db.add(row)
        self.audit.record(user, "COMPENSATION_CREATED", "compensation", row.id, {"case_id": str(case.id)})
        self.notes.notify_roles(
            ["ACQUISITION_OFFICER", "ADMIN"],
            "Compensation updated",
            f"Compensation recorded for case {case.case_number}",
            "acquisition_case",
            str(case.id),
            exclude_user_id=user.id,
        )
        self.db.commit()
        return _serialize(row)

    def update(self, user: User, case_id: UUID, body) -> dict:
        self._case(user, case_id)
        row = self.db.scalars(
            select(Compensation).where(Compensation.acquisition_case_id == case_id)
        ).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Compensation record not found")
        data = body.model_dump(exclude_unset=True)
        assessed = float(data.get("assessed_amount_inr", row.assessed_amount_inr or 0))
        paid = float(data.get("paid_amount_inr", row.paid_amount_inr or 0))
        if assessed < 0 or paid < 0:
            raise AppError(400, "VALIDATION_ERROR", "Amounts must be >= 0")
        if paid > assessed:
            raise AppError(400, "VALIDATION_ERROR", "paid_amount cannot exceed assessed_amount")
        for key, value in data.items():
            setattr(row, key, value)
        row.status = data.get("status") or _status(assessed, paid)
        self.audit.record(user, "COMPENSATION_UPDATED", "compensation", row.id, {"case_id": str(case_id)})
        self.db.commit()
        return _serialize(row)
