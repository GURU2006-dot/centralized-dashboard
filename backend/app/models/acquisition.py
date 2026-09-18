"""Acquisition cases and append-only workflow events.

Case stages are the post-approval lifecycle only (SIA → … → COMPLETED).
Proposal approval is *not* performed by transitioning a case.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, TimestampMixin


class WorkflowStageDefinition(Base):
    __tablename__ = "workflow_stage_definitions"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    expected_duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)


class AcquisitionCase(TimestampMixin, Base):
    __tablename__ = "acquisition_cases"
    __table_args__ = (
        UniqueConstraint("project_id", "parcel_id", name="uq_acquisition_cases_project_parcel"),
        Index("ix_acquisition_cases_project_stage_status", "project_id", "current_stage", "status"),
        Index("ix_acquisition_cases_parcel_id", "parcel_id"),
        CheckConstraint(
            "status IN ('OPEN','ON_HOLD','CLOSED','DROPPED')",
            name="ck_cases_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_cases_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("land_parcels.id"), nullable=False)
    proposal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("proposals.id"), nullable=True)
    current_stage: Mapped[str] = mapped_column(
        ForeignKey("workflow_stage_definitions.code"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="OPEN")
    notified_area_ha: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    acquired_area_ha: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    stage_entered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_stage_exit_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    project: Mapped["Project"] = relationship(back_populates="acquisition_cases")
    parcel: Mapped["LandParcel"] = relationship(back_populates="acquisition_cases")
    proposal: Mapped["Proposal | None"] = relationship(back_populates="acquisition_cases")
    events: Mapped[list[WorkflowEvent]] = relationship(
        back_populates="acquisition_case", order_by="WorkflowEvent.occurred_at"
    )


class WorkflowEvent(CreatedAtMixin, Base):
    """Append-only. UPDATE and DELETE are blocked by a database trigger."""

    __tablename__ = "workflow_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    acquisition_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("acquisition_cases.id"), nullable=False, index=True
    )
    from_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(40), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", use_alter=True, name="fk_workflow_events_document_id"),
        nullable=True,
    )
    extra_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )

    acquisition_case: Mapped[AcquisitionCase] = relationship(back_populates="events")
