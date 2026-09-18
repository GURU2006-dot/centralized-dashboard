"""Possession of acquired land (0..1 per case)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Possession(TimestampMixin, Base):
    __tablename__ = "possession"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NOT_TAKEN','PARTIAL','TAKEN')",
            name="ck_possession_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_possession_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    acquisition_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("acquisition_cases.id"), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_TAKEN")
    area_ha: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    taken_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String, nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    acquisition_case: Mapped["AcquisitionCase"] = relationship()
