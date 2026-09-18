"""Affected families, rehabilitation, and resettlement."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AffectedFamily(TimestampMixin, Base):
    __tablename__ = "affected_families"
    __table_args__ = (
        CheckConstraint("member_count > 0", name="ck_families_member_count"),
        CheckConstraint(
            "status IN ('IDENTIFIED','ASSISTED','RESETTLED','CLOSED')",
            name="ck_families_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_families_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    parcel_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("land_parcels.id"), nullable=True
    )
    family_head_name: Mapped[str] = mapped_column(String(255), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_displaced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contact: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="IDENTIFIED")
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    rehabilitation: Mapped[Rehabilitation | None] = relationship(back_populates="family")
    resettlement: Mapped[Resettlement | None] = relationship(back_populates="family")


class Rehabilitation(TimestampMixin, Base):
    __tablename__ = "rehabilitation"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NOT_STARTED','IN_PROGRESS','COMPLETED')",
            name="ck_rehab_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_rehab_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    family_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("affected_families.id"), unique=True, nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    package_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount_inr: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="NOT_STARTED")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    family: Mapped[AffectedFamily] = relationship(back_populates="rehabilitation")


class Resettlement(TimestampMixin, Base):
    __tablename__ = "resettlement"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NOT_ALLOTTED','ALLOTTED','POSSESSED')",
            name="ck_resettlement_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_resettlement_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    family_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("affected_families.id"), unique=True, nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    site_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    plot_allotted: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="NOT_ALLOTTED")
    allotted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    possession_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    family: Mapped[AffectedFamily] = relationship(back_populates="resettlement")
