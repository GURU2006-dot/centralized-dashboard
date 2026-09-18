from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.field_verification import FieldVerification
from app.models.user import User
from app.schemas.common import as_float
from app.services.audit import AuditService
from app.services.notifications import NotificationService
from app.services.scope import role_code


def _serialize(row: FieldVerification) -> dict:
    return {
        "id": row.id,
        "parcel_id": row.parcel_id,
        "acquisition_case_id": row.acquisition_case_id,
        "assigned_to": row.assigned_to,
        "status": row.status,
        "gps_lat": as_float(row.gps_lat),
        "gps_lng": as_float(row.gps_lng),
        "captured_at": row.captured_at,
        "owner_verified": row.owner_verified,
        "land_info_verified": row.land_info_verified,
        "documents_verified": row.documents_verified,
        "remarks": row.remarks,
        "submitted_at": row.submitted_at,
        "data_source": row.data_source,
    }


class FieldVerificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.notes = NotificationService(db)

    def _stmt(self, user: User):
        stmt = select(FieldVerification)
        if role_code(user) == "FIELD_OFFICER":
            stmt = stmt.where(FieldVerification.assigned_to == user.id)
        return stmt

    def list_rows(self, user: User, *, status: str | None, page: int, page_size: int):
        stmt = self._stmt(user)
        if status:
            stmt = stmt.where(FieldVerification.status == status)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(FieldVerification.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return [_serialize(r) for r in rows], int(total)

    def get(self, user: User, rec_id: UUID) -> FieldVerification:
        row = self.db.scalars(self._stmt(user).where(FieldVerification.id == rec_id)).first()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Field verification not found")
        return row

    def get_dict(self, user: User, rec_id: UUID) -> dict:
        return _serialize(self.get(user, rec_id))

    def update(self, user: User, rec_id: UUID, body) -> dict:
        row = self.get(user, rec_id)
        if role_code(user) == "FIELD_OFFICER" and row.assigned_to != user.id:
            raise AppError(403, "FORBIDDEN", "Not assigned to this verification")
        if row.status == "SUBMITTED":
            raise AppError(409, "CONFLICT", "Verification already submitted")
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        if row.gps_lat is not None and row.gps_lng is not None and row.captured_at is None:
            row.captured_at = datetime.now(timezone.utc)
        if row.status == "ASSIGNED":
            row.status = "IN_PROGRESS"
        self.db.commit()
        return _serialize(row)

    def submit(self, user: User, rec_id: UUID, remarks: str | None) -> dict:
        row = self.get(user, rec_id)
        if role_code(user) == "FIELD_OFFICER" and row.assigned_to != user.id:
            raise AppError(403, "FORBIDDEN", "Not assigned to this verification")
        if row.status == "SUBMITTED":
            raise AppError(409, "CONFLICT", "Verification already submitted")
        if row.gps_lat is None or row.gps_lng is None:
            raise AppError(400, "VALIDATION_ERROR", "GPS coordinates are required to submit")
        if row.owner_verified is None or row.land_info_verified is None or row.documents_verified is None:
            raise AppError(
                400,
                "VALIDATION_ERROR",
                "Owner, land-info, and document verification flags are required",
            )
        now = datetime.now(timezone.utc)
        row.status = "SUBMITTED"
        row.submitted_at = now
        row.submitted_by = user.id
        row.captured_at = row.captured_at or now
        if remarks:
            row.remarks = remarks
        self.audit.record(
            user,
            "FIELD_VERIFICATION_SUBMITTED",
            "field_verification",
            row.id,
            {"parcel_id": str(row.parcel_id), "gps": [float(row.gps_lat), float(row.gps_lng)]},
        )
        self.notes.notify_roles(
            ["ACQUISITION_OFFICER", "ADMIN"],
            "Field verification completed",
            f"Verification {row.id} submitted.",
            "field_verification",
            str(row.id),
        )
        self.db.commit()
        return _serialize(row)
