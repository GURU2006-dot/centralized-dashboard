"""Field verification assignments."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FieldVerification(TimestampMixin, Base):
    __tablename__ = "field_verifications"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ASSIGNED','IN_PROGRESS','SUBMITTED','ACCEPTED','REJECTED')",
            name="ck_field_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_field_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("land_parcels.id"), nullable=False)
    acquisition_case_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("acquisition_cases.id"), nullable=True
    )
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ASSIGNED")
    gps_lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    land_info_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    documents_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    remarks: Mapped[str | None] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )
