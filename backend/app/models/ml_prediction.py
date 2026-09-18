"""Persisted delay-risk scores.

risk_score is the model's numeric risk score (0–1), NOT a calibrated probability
of delay unless a later evaluation phase demonstrates calibration.
trained_on is SYNTHETIC for this prototype.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    __table_args__ = (
        CheckConstraint("risk_level IN ('LOW','MEDIUM','HIGH')", name="ck_ml_risk_level"),
        CheckConstraint("risk_score >= 0 AND risk_score <= 1", name="ck_ml_risk_score"),
        CheckConstraint(
            "trained_on IN ('SYNTHETIC','AUTHORIZED_HISTORICAL')",
            name="ck_ml_trained_on",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    acquisition_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("acquisition_cases.id"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(8), nullable=False)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    trained_on: Mapped[str] = mapped_column(
        String(16), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    predicted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
