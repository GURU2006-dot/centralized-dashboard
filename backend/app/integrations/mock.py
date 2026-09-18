from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.integrations.base import (
    AdapterError,
    AdapterHealth,
    NormalizedCadastralFeature,
    NormalizedOwner,
    NormalizedParcel,
    NormalizedPayment,
    NormalizedRegistration,
)
from app.models.acquisition import AcquisitionCase
from app.models.compensation import Compensation
from app.models.parcel import LandParcel, ParcelOwner
from app.schemas.common import SYNTHETIC_DISCLAIMER


def _health(name: str) -> AdapterHealth:
    return AdapterHealth(
        name=name,
        implementation="MOCK",
        availability="UNAVAILABLE_PUBLIC",
        requires_authorization=True,
        healthy=True,
        mode="MOCK",
        message="No public API. Mock adapter serving synthetic records. MOCK / DEMONSTRATION.",
    )


def _parcel(db: Session, ulpin: str) -> LandParcel:
    row = db.scalars(
        select(LandParcel)
        .options(selectinload(LandParcel.ownerships).selectinload(ParcelOwner.owner))
        .where(LandParcel.ulpin == ulpin)
    ).first()
    if row is None:
        raise AdapterError("NOT_FOUND", "ULPIN not found in mock store", 404)
    return row


class MockLandRecordsAdapter:
    name = "land_records"

    def __init__(self, db: Session) -> None:
        self.db = db

    def health(self) -> AdapterHealth:
        return _health(self.name)

    def lookup(self, *, ulpin: str) -> NormalizedParcel:
        p = _parcel(self.db, ulpin)
        owners = []
        for link in p.ownerships:
            owners.append(
                NormalizedOwner(
                    name=link.owner.name if link.owner else "Unknown",
                    share_pct=float(link.ownership_share_pct) if link.ownership_share_pct is not None else None,
                    ownership_type=link.ownership_type,
                )
            )
        return NormalizedParcel(
            ulpin=p.ulpin,
            khasra_number=p.khasra_number,
            village=p.village,
            tehsil=p.tehsil,
            state_code=p.state_code,
            district_code=p.district_code,
            area_ha=float(p.area_ha),
            owners=owners,
            data_source="MOCK_ADAPTER",
            fetched_at=datetime.now(timezone.utc),
            raw_reference=f"mock:{p.id}",
        )


class MockCadastralAdapter:
    name = "cadastral_maps"

    def __init__(self, db: Session) -> None:
        self.db = db

    def health(self) -> AdapterHealth:
        return _health(self.name)

    def get_parcel_geometry(self, ulpin: str) -> NormalizedCadastralFeature:
        p = _parcel(self.db, ulpin)
        return NormalizedCadastralFeature(
            ulpin=p.ulpin,
            geometry_geojson=p.geometry_geojson,
            srid=4326,
            data_source="MOCK_ADAPTER",
            disclaimer=f"MOCK / DEMONSTRATION. {SYNTHETIC_DISCLAIMER}",
        )


class MockRegistrationAdapter:
    name = "registration"

    def __init__(self, db: Session) -> None:
        self.db = db

    def health(self) -> AdapterHealth:
        return _health(self.name)

    def lookup_by_ulpin(self, ulpin: str) -> NormalizedRegistration:
        _parcel(self.db, ulpin)
        return NormalizedRegistration(
            ulpin=ulpin,
            last_deed_date=date(2020, 1, 15),
            last_deed_type="SALE_DEED_SYNTHETIC",
            data_source="MOCK_ADAPTER",
        )


class MockFinancialAdapter:
    name = "financial"

    def __init__(self, db: Session) -> None:
        self.db = db

    def health(self) -> AdapterHealth:
        return _health(self.name)

    def payment_status(self, ulpin: str) -> NormalizedPayment:
        p = _parcel(self.db, ulpin)
        case = self.db.scalars(
            select(AcquisitionCase).where(AcquisitionCase.parcel_id == p.id)
        ).first()
        status = None
        assessed = None
        paid = None
        if case:
            comp = self.db.scalars(
                select(Compensation).where(Compensation.acquisition_case_id == case.id)
            ).first()
            if comp:
                status = comp.status
                assessed = float(comp.assessed_amount_inr or 0)
                paid = float(comp.paid_amount_inr or 0)
        return NormalizedPayment(
            ulpin=ulpin,
            compensation_status=status,
            assessed_amount_inr=assessed,
            paid_amount_inr=paid,
            data_source="MOCK_ADAPTER",
        )


class ExternalUnavailableAdapter:
    """Stub for INTEGRATION_MODE=external. Always fails closed."""

    def __init__(self, name: str) -> None:
        self.name = name

    def health(self) -> AdapterHealth:
        return AdapterHealth(
            name=self.name,
            implementation="EXTERNAL",
            availability="REQUIRES_AUTHORIZATION",
            requires_authorization=True,
            healthy=False,
            mode="EXTERNAL",
            message="No authorized government connection is configured. Refusing to invent an endpoint.",
        )

    def lookup(self, **kwargs):
        raise AdapterError("INTEGRATION_UNAVAILABLE", self.health().message, 503)

    def get_parcel_geometry(self, ulpin: str):
        raise AdapterError("INTEGRATION_UNAVAILABLE", self.health().message, 503)

    def lookup_by_ulpin(self, ulpin: str):
        raise AdapterError("INTEGRATION_UNAVAILABLE", self.health().message, 503)

    def payment_status(self, ulpin: str):
        raise AdapterError("INTEGRATION_UNAVAILABLE", self.health().message, 503)
