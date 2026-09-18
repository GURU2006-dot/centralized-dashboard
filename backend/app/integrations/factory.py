from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import INTEGRATION_MODE
from app.integrations.mock import (
    ExternalUnavailableAdapter,
    MockCadastralAdapter,
    MockFinancialAdapter,
    MockLandRecordsAdapter,
    MockRegistrationAdapter,
)


def land_records(db: Session):
    if INTEGRATION_MODE != "mock":
        return ExternalUnavailableAdapter("land_records")
    return MockLandRecordsAdapter(db)


def cadastral(db: Session):
    if INTEGRATION_MODE != "mock":
        return ExternalUnavailableAdapter("cadastral_maps")
    return MockCadastralAdapter(db)


def registration(db: Session):
    if INTEGRATION_MODE != "mock":
        return ExternalUnavailableAdapter("registration")
    return MockRegistrationAdapter(db)


def financial(db: Session):
    if INTEGRATION_MODE != "mock":
        return ExternalUnavailableAdapter("financial")
    return MockFinancialAdapter(db)
