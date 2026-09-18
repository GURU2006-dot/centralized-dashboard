from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.family import AffectedFamily, Rehabilitation, Resettlement
from app.models.user import User
from app.repositories.acquisitions import AcquisitionRepository
from app.schemas.common import as_float
from app.services.audit import AuditService


class RRService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cases = AcquisitionRepository(db)
        self.audit = AuditService(db)

    def _case(self, user: User, case_id: UUID):
        case = self.cases.get_scoped(user, case_id)
        if case is None:
            raise AppError(404, "NOT_FOUND", "Acquisition case not found")
        return case

    def _families_for_case(self, case) -> list[AffectedFamily]:
        parcel_fams = list(
            self.db.scalars(
                select(AffectedFamily).where(AffectedFamily.parcel_id == case.parcel_id)
            ).all()
        )
        if parcel_fams:
            return parcel_fams
        return list(
            self.db.scalars(
                select(AffectedFamily).where(AffectedFamily.project_id == case.project_id)
            ).all()
        )

    def rehabilitation_for_case(self, user: User, case_id: UUID) -> list[dict]:
        case = self._case(user, case_id)
        fams = self._families_for_case(case)
        ids = [f.id for f in fams]
        if not ids:
            return []
        rows = list(
            self.db.scalars(select(Rehabilitation).where(Rehabilitation.family_id.in_(ids))).all()
        )
        return [self._ser_rehab(r) for r in rows]

    def resettlement_for_case(self, user: User, case_id: UUID) -> list[dict]:
        case = self._case(user, case_id)
        fams = self._families_for_case(case)
        ids = [f.id for f in fams]
        if not ids:
            return []
        rows = list(
            self.db.scalars(select(Resettlement).where(Resettlement.family_id.in_(ids))).all()
        )
        return [self._ser_reset(r) for r in rows]

    def create_rehab(self, user: User, body) -> dict:
        family = self.db.get(AffectedFamily, body.family_id)
        if family is None:
            raise AppError(404, "NOT_FOUND", "Family not found")
        existing = self.db.scalars(
            select(Rehabilitation).where(Rehabilitation.family_id == family.id)
        ).first()
        if existing:
            raise AppError(409, "CONFLICT", "Rehabilitation already exists for this family")
        row = Rehabilitation(
            id=uuid4(),
            family_id=family.id,
            project_id=family.project_id,
            package_type=body.package_type,
            amount_inr=body.amount_inr,
            status=body.status or "NOT_STARTED",
            start_date=body.start_date,
            completion_date=body.completion_date,
            data_source="SYNTHETIC",
        )
        self.db.add(row)
        self.audit.record(user, "RR_UPDATED", "rehabilitation", row.id, {"family_id": str(family.id)})
        self.db.commit()
        return self._ser_rehab(row)

    def patch_rehab(self, user: User, rec_id: UUID, body) -> dict:
        row = self.db.get(Rehabilitation, rec_id)
        if row is None:
            # treat as case_id
            items = self.rehabilitation_for_case(user, rec_id)
            if not items:
                raise AppError(404, "NOT_FOUND", "Rehabilitation record not found")
            row = self.db.get(Rehabilitation, items[0]["id"])
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        self.audit.record(user, "RR_UPDATED", "rehabilitation", row.id)
        self.db.commit()
        return self._ser_rehab(row)

    def create_reset(self, user: User, body) -> dict:
        family = self.db.get(AffectedFamily, body.family_id)
        if family is None:
            raise AppError(404, "NOT_FOUND", "Family not found")
        existing = self.db.scalars(
            select(Resettlement).where(Resettlement.family_id == family.id)
        ).first()
        if existing:
            raise AppError(409, "CONFLICT", "Resettlement already exists for this family")
        row = Resettlement(
            id=uuid4(),
            family_id=family.id,
            project_id=family.project_id,
            site_name=body.site_name,
            plot_allotted=body.plot_allotted,
            status=body.status or "NOT_ALLOTTED",
            allotted_date=body.allotted_date,
            possession_date=body.possession_date,
            data_source="SYNTHETIC",
        )
        self.db.add(row)
        self.audit.record(user, "RR_UPDATED", "resettlement", row.id, {"family_id": str(family.id)})
        self.db.commit()
        return self._ser_reset(row)

    def patch_reset(self, user: User, rec_id: UUID, body) -> dict:
        row = self.db.get(Resettlement, rec_id)
        if row is None:
            items = self.resettlement_for_case(user, rec_id)
            if not items:
                raise AppError(404, "NOT_FOUND", "Resettlement record not found")
            row = self.db.get(Resettlement, items[0]["id"])
        data = body.model_dump(exclude_unset=True)
        mapping = {"site_name": "site_name", "plot_allotted": "plot_allotted"}
        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        self.audit.record(user, "RR_UPDATED", "resettlement", row.id)
        self.db.commit()
        return self._ser_reset(row)

    @staticmethod
    def _ser_rehab(row: Rehabilitation) -> dict:
        return {
            "id": row.id,
            "family_id": row.family_id,
            "project_id": row.project_id,
            "package_type": row.package_type,
            "amount_inr": as_float(row.amount_inr),
            "status": row.status,
            "start_date": row.start_date,
            "completion_date": row.completion_date,
            "data_source": row.data_source,
        }

    @staticmethod
    def _ser_reset(row: Resettlement) -> dict:
        return {
            "id": row.id,
            "family_id": row.family_id,
            "project_id": row.project_id,
            "site_name": row.site_name,
            "plot_allotted": row.plot_allotted,
            "status": row.status,
            "allotted_date": row.allotted_date,
            "possession_date": row.possession_date,
            "data_source": row.data_source,
        }
