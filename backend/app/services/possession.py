from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.possession import Possession
from app.models.user import User
from app.repositories.acquisitions import AcquisitionRepository
from app.schemas.common import as_float
from app.services.audit import AuditService


def _serialize(row: Possession) -> dict:
    return {
        "id": row.id,
        "acquisition_case_id": row.acquisition_case_id,
        "status": row.status,
        "area_ha": as_float(row.area_ha),
        "taken_at": row.taken_at,
        "taken_by": row.taken_by,
        "remarks": row.remarks,
        "data_source": row.data_source,
    }


class PossessionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cases = AcquisitionRepository(db)
        self.audit = AuditService(db)

    def _case(self, user: User, case_id: UUID):
        case = self.cases.get_scoped(user, case_id)
        if case is None:
            raise AppError(404, "NOT_FOUND", "Acquisition case not found")
        return case

    def get(self, user: User, case_id: UUID) -> dict:
        self._case(user, case_id)
        row = self.db.scalars(
            select(Possession).where(Possession.acquisition_case_id == case_id)
        ).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Possession record not found")
        return _serialize(row)

    def create(self, user: User, body) -> dict:
        case = self._case(user, body.acquisition_case_id)
        existing = self.db.scalars(
            select(Possession).where(Possession.acquisition_case_id == case.id)
        ).first()
        if existing:
            raise AppError(409, "CONFLICT", "Possession already exists for this case")
        area = body.area_ha
        if area is not None and case.parcel and float(area) > float(case.parcel.area_ha) + 1e-6:
            raise AppError(400, "VALIDATION_ERROR", "Possessed area cannot exceed parcel area")
        row = Possession(
            id=uuid4(),
            acquisition_case_id=case.id,
            status=body.status or "NOT_TAKEN",
            area_ha=area,
            taken_at=body.taken_at,
            taken_by=user.id,
            remarks=body.remarks,
            data_source="SYNTHETIC",
        )
        self.db.add(row)
        self.audit.record(user, "POSSESSION_CREATED", "possession", row.id, {"case_id": str(case.id)})
        self.db.commit()
        return _serialize(row)

    def update(self, user: User, case_id: UUID, body) -> dict:
        case = self._case(user, case_id)
        row = self.db.scalars(
            select(Possession).where(Possession.acquisition_case_id == case_id)
        ).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Possession record not found")
        data = body.model_dump(exclude_unset=True)
        if "area_ha" in data and data["area_ha"] is not None and case.parcel:
            if float(data["area_ha"]) > float(case.parcel.area_ha) + 1e-6:
                raise AppError(400, "VALIDATION_ERROR", "Possessed area cannot exceed parcel area")
        for key, value in data.items():
            setattr(row, key, value)
        self.audit.record(user, "POSSESSION_UPDATED", "possession", row.id, {"case_id": str(case_id)})
        self.db.commit()
        return _serialize(row)
