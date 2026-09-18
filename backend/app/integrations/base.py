"""Internal adapter contracts. No invented government URLs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Protocol

Availability = Literal[
    "AVAILABLE_VERIFIED",
    "REQUIRES_AUTHORIZATION",
    "UNAVAILABLE_PUBLIC",
    "MOCK_ONLY",
]
Implementation = Literal["MOCK", "EXTERNAL"]
DataOrigin = Literal["MOCK_ADAPTER", "EXTERNAL"]


@dataclass
class AdapterHealth:
    name: str
    implementation: Implementation
    availability: Availability
    requires_authorization: bool
    healthy: bool
    message: str
    mode: str = "MOCK"


@dataclass
class NormalizedOwner:
    name: str
    share_pct: float | None
    ownership_type: str | None


@dataclass
class NormalizedParcel:
    ulpin: str
    khasra_number: str
    village: str | None
    tehsil: str | None
    state_code: str
    district_code: str
    area_ha: float
    owners: list[NormalizedOwner] = field(default_factory=list)
    data_source: DataOrigin = "MOCK_ADAPTER"
    fetched_at: datetime | None = None
    raw_reference: str = "mock"


@dataclass
class NormalizedCadastralFeature:
    ulpin: str
    geometry_geojson: dict | None
    srid: int = 4326
    data_source: DataOrigin = "MOCK_ADAPTER"
    disclaimer: str = "MOCK / DEMONSTRATION"


@dataclass
class NormalizedRegistration:
    ulpin: str
    last_deed_date: date | None
    last_deed_type: str | None
    data_source: DataOrigin = "MOCK_ADAPTER"


@dataclass
class NormalizedPayment:
    ulpin: str
    compensation_status: str | None
    assessed_amount_inr: float | None
    paid_amount_inr: float | None
    data_source: DataOrigin = "MOCK_ADAPTER"


class AdapterError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class LandRecordsPort(Protocol):
    name: str

    def health(self) -> AdapterHealth: ...
    def lookup(self, *, ulpin: str) -> NormalizedParcel: ...


class CadastralPort(Protocol):
    name: str

    def health(self) -> AdapterHealth: ...
    def get_parcel_geometry(self, ulpin: str) -> NormalizedCadastralFeature: ...


class RegistrationPort(Protocol):
    name: str

    def health(self) -> AdapterHealth: ...
    def lookup_by_ulpin(self, ulpin: str) -> NormalizedRegistration: ...


class FinancialPort(Protocol):
    name: str

    def health(self) -> AdapterHealth: ...
    def payment_status(self, ulpin: str) -> NormalizedPayment: ...
