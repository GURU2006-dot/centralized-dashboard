from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.user import User
from app.repositories.acquisitions import AcquisitionRepository
from app.schemas.common import as_float


class AcquisitionService:
    def __init__(self, db: Session) -> None:
        self.repo = AcquisitionRepository(db)

    def list_cases(self, user: User, **kwargs) -> tuple[list[dict], int]:
        rows, total = self.repo.list_filtered(user, **kwargs)
        data = []
        for case, project, parcel, risk_level, risk_score in rows:
            data.append(
                {
                    "id": case.id,
                    "case_number": case.case_number,
                    "project_id": project.id,
                    "project_code": project.code,
                    "parcel_id": parcel.id,
                    "ulpin": parcel.ulpin,
                    "current_stage": case.current_stage,
                    "status": case.status,
                    "notified_area_ha": as_float(case.notified_area_ha),
                    "acquired_area_ha": as_float(case.acquired_area_ha),
                    "risk_level": risk_level,
                    "risk_score": as_float(risk_score),
                    "data_source": case.data_source,
                }
            )
        return data, total

    def get(self, user: User, case_id: UUID) -> dict:
        case = self.repo.get_scoped(user, case_id)
        if case is None:
            raise AppError(404, "NOT_FOUND", "Acquisition case not found")
        comp = self.repo.compensation(case.id)
        poss = self.repo.possession(case.id)
        rr = self.repo.rr_for_project(case.project_id)
        risk = self.repo.latest_risk(case.id)
        return {
            "id": case.id,
            "case_number": case.case_number,
            "project_id": case.project_id,
            "project_code": case.project.code,
            "project_name": case.project.name,
            "parcel_id": case.parcel_id,
            "ulpin": case.parcel.ulpin,
            "khasra_number": case.parcel.khasra_number,
            "current_stage": case.current_stage,
            "status": case.status,
            "notified_area_ha": as_float(case.notified_area_ha),
            "acquired_area_ha": as_float(case.acquired_area_ha),
            "started_at": case.started_at,
            "completed_at": case.completed_at,
            "compensation": (
                {
                    "assessed_amount_inr": as_float(comp.assessed_amount_inr),
                    "paid_amount_inr": as_float(comp.paid_amount_inr),
                    "status": comp.status,
                }
                if comp
                else None
            ),
            "possession": (
                {"status": poss.status, "area_ha": as_float(poss.area_ha)} if poss else None
            ),
            "rr": rr,
            "risk_level": risk[0] if risk else None,
            "risk_score": risk[1] if risk else None,
            "data_source": case.data_source,
        }

    def timeline(self, user: User, case_id: UUID) -> dict:
        case = self.repo.get_scoped(user, case_id)
        if case is None:
            raise AppError(404, "NOT_FOUND", "Acquisition case not found")
        events = []
        for event, actor in self.repo.timeline(case.id):
            events.append(
                {
                    "id": event.id,
                    "from_stage": event.from_stage,
                    "to_stage": event.to_stage,
                    "occurred_at": event.occurred_at,
                    "actor_id": actor.id if actor else None,
                    "actor_name": actor.full_name if actor else None,
                    "remarks": event.remarks,
                }
            )
        return {"stages": self.repo.stage_codes(), "events": events}
