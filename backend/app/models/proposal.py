"""Acquisition proposals.

Proposal approval (status APPROVED / REJECTED) is the *authoritative* approval
action. Acquisition cases are created/activated only after APPROVED. Case
workflow stages do not include a second approve/reject action.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Proposal(TimestampMixin, Base):
    __tablename__ = "proposals"
    __table_args__ = (
        CheckConstraint("required_area_ha >= 0", name="ck_proposals_area_nonneg"),
        CheckConstraint(
            "affected_families_count >= 0", name="ck_proposals_families_nonneg"
        ),
        CheckConstraint(
            "status IN ('DRAFT','SUBMITTED','UNDER_VERIFICATION','APPROVED','REJECTED')",
            name="ck_proposals_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_proposals_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    proposal_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    required_area_ha: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    purpose: Mapped[str] = mapped_column(String, nullable=False)
    estimated_compensation_inr: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    affected_families_count: Mapped[int | None] = mapped_column(nullable=True)
    proposed_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    proposed_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_remarks: Mapped[str | None] = mapped_column(String, nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    project: Mapped["Project"] = relationship(back_populates="proposals")
    parcels: Mapped[list[ProposalParcel]] = relationship(
        back_populates="proposal", cascade="all, delete-orphan"
    )
    acquisition_cases: Mapped[list["AcquisitionCase"]] = relationship(back_populates="proposal")


class ProposalParcel(Base):
    __tablename__ = "proposal_parcels"

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE"), primary_key=True
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("land_parcels.id"), primary_key=True
    )

    proposal: Mapped[Proposal] = relationship(back_populates="parcels")
    parcel: Mapped["LandParcel"] = relationship()
