"""Land parcels, owners, and M:N ownership."""

from __future__ import annotations

import uuid

from geoalchemy2 import Geography, Geometry
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class LandParcel(TimestampMixin, Base):
    __tablename__ = "land_parcels"
    __table_args__ = (
        CheckConstraint("area_ha > 0", name="ck_parcels_area_positive"),
        CheckConstraint(
            "acquisition_status IN ('NOT_STARTED','IN_PROCESS','ACQUIRED','DISPUTED','DROPPED')",
            name="ck_parcels_acq_status",
        ),
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_parcels_data_source",
        ),
        Index("ix_land_parcels_khasra_number", "khasra_number"),
        Index("ix_land_parcels_state_district", "state_code", "district_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ulpin: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    khasra_number: Mapped[str] = mapped_column(String(64), nullable=False)
    village: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tehsil: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state_code: Mapped[str] = mapped_column(ForeignKey("states.code"), nullable=False)
    district_code: Mapped[str] = mapped_column(ForeignKey("districts.code"), nullable=False)
    area_ha: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"), nullable=True, index=True
    )
    acquisition_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="NOT_STARTED"
    )
    current_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    centroid: Mapped[object | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    geom: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True
    )
    geometry_geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    project: Mapped["Project | None"] = relationship(back_populates="parcels")
    ownerships: Mapped[list[ParcelOwner]] = relationship(
        back_populates="parcel", cascade="all, delete-orphan"
    )
    acquisition_cases: Mapped[list["AcquisitionCase"]] = relationship(back_populates="parcel")


class Owner(TimestampMixin, Base):
    """Owner identity. Sensitive fields (id_number, phone, address) are stored
    for authorized contexts only — they must not be included in general parcel APIs.
    """

    __tablename__ = "owners"
    __table_args__ = (
        CheckConstraint(
            "data_source IN ('SYNTHETIC','MOCK_ADAPTER','EXTERNAL')",
            name="ck_owners_data_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    father_or_spouse_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    id_type: Mapped[str | None] = mapped_column(String(24), nullable=True)
    id_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SYNTHETIC", server_default="SYNTHETIC"
    )

    ownerships: Mapped[list[ParcelOwner]] = relationship(back_populates="owner")


class ParcelOwner(Base):
    __tablename__ = "parcel_owners"
    __table_args__ = (
        CheckConstraint(
            "ownership_share_pct >= 0 AND ownership_share_pct <= 100",
            name="ck_parcel_owners_share",
        ),
        CheckConstraint(
            "ownership_type IN ('SOLE','JOINT','LEGAL_HEIR','ENCUMBERED')",
            name="ck_parcel_owners_type",
        ),
    )

    parcel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("land_parcels.id", ondelete="CASCADE"), primary_key=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("owners.id"), primary_key=True)
    ownership_share_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    ownership_type: Mapped[str] = mapped_column(String(24), nullable=False, default="SOLE")

    parcel: Mapped[LandParcel] = relationship(back_populates="ownerships")
    owner: Mapped[Owner] = relationship(back_populates="ownerships")
