"""Administrative geography lookups."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class State(Base):
    __tablename__ = "states"

    code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    centroid_lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    centroid_lng: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)

    districts: Mapped[list[District]] = relationship(back_populates="state")


class District(Base):
    __tablename__ = "districts"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    state_code: Mapped[str] = mapped_column(ForeignKey("states.code"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

    state: Mapped[State] = relationship(back_populates="districts")
