from __future__ import annotations

from dataclasses import asdict

from sqlalchemy.orm import Session

from app.config import INTEGRATION_MODE
from app.errors import AppError
from app.integrations import factory
from app.integrations.base import AdapterError
from app.models.user import User
from app.services.audit import AuditService


class IntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def status(self) -> dict:
        adapters = [
            factory.land_records(self.db),
            factory.cadastral(self.db),
            factory.registration(self.db),
            factory.financial(self.db),
        ]
        return {
            "mode": INTEGRATION_MODE,
            "disclaimer": (
                "Government land-record, cadastral, registration, and financial APIs "
                "require departmental authorization and are not connected. "
                "Adapters use the same internal interfaces a future authorized connection would use. "
                "MOCK / DEMONSTRATION."
            ),
            "systems": [asdict(a.health()) for a in adapters],
        }

    def lookup(self, user: User, system: str, ulpin: str) -> dict:
        ulpin = (ulpin or "").strip()
        if not ulpin:
            raise AppError(400, "VALIDATION_ERROR", "ulpin is required")
        try:
            if system == "land-records":
                data = factory.land_records(self.db).lookup(ulpin=ulpin)
            elif system == "cadastral":
                data = factory.cadastral(self.db).get_parcel_geometry(ulpin)
            elif system == "registration":
                data = factory.registration(self.db).lookup_by_ulpin(ulpin)
            elif system == "financial":
                data = factory.financial(self.db).payment_status(ulpin)
            else:
                raise AppError(404, "NOT_FOUND", "Unknown integration system")
        except AdapterError as exc:
            raise AppError(exc.status, exc.code, exc.message) from exc
        payload = asdict(data)
        payload["mode"] = "MOCK"
        payload["badge"] = "MOCK / DEMONSTRATION"
        self.audit.record(user, "INTEGRATION_LOOKUP", "integration", ulpin, {"system": system, "mode": "MOCK"})
        self.db.commit()
        return payload

    def sync(self, user: User, system: str) -> dict:
        health = None
        mapping = {
            "land-records": factory.land_records,
            "cadastral": factory.cadastral,
            "registration": factory.registration,
            "financial": factory.financial,
        }
        if system not in mapping:
            raise AppError(404, "NOT_FOUND", "Unknown integration system")
        health = mapping[system](self.db).health()
        self.audit.record(user, "INTEGRATION_SYNC", "integration", system, {"mode": "MOCK"})
        self.db.commit()
        return {
            "system": system,
            "mode": "MOCK",
            "synced": 0,
            "message": "Mock sync does not write live government data. No records were imported.",
            "health": asdict(health),
        }
