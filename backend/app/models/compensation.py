"""Compensation per acquisition case (0..1)."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Compensation(TimestampMixin, Base):
    __tablename__ = "compensation"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NOT_ASSESSED','ASSESSED','PARTIAL','PAID','DISPUTED')",
            name="ck_compensation_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_compensation_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    acquisition_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("acquisition_cases.id"), unique=True, nullable=False
    )
    assessed_amount_inr: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    paid_amount_inr: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False, default=0, server_default="0"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_ASSESSED")
    assessment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remarks: Mapped[str | None] = mapped_column(String, nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    acquisition_case: Mapped["AcquisitionCase"] = relationship()
