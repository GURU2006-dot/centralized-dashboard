"""Projects."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("estimated_area_ha >= 0", name="ck_projects_area_nonneg"),
        CheckConstraint(
            "estimated_compensation_inr >= 0", name="ck_projects_comp_nonneg"
        ),
        CheckConstraint(
            "status IN ('PLANNED','ACTIVE','DELAYED','ON_HOLD','COMPLETED')",
            name="ck_projects_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_projects_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String, nullable=False)
    requiring_body: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state_code: Mapped[str] = mapped_column(ForeignKey("states.code"), nullable=False, index=True)
    district_code: Mapped[str | None] = mapped_column(ForeignKey("districts.code"), nullable=True)
    estimated_area_ha: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    estimated_compensation_inr: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    current_stage: Mapped[str | None] = mapped_column(
        ForeignKey("workflow_stage_definitions.code"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    parcels: Mapped[list["LandParcel"]] = relationship(back_populates="project")
    proposals: Mapped[list["Proposal"]] = relationship(back_populates="project")
    acquisition_cases: Mapped[list["AcquisitionCase"]] = relationship(back_populates="project")
