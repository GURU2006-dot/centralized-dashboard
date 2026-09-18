from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AcquisitionListItem(BaseModel):
    id: UUID
    case_number: str
    project_id: UUID
    project_code: str
    parcel_id: UUID
    ulpin: str
    current_stage: str
    status: str
    notified_area_ha: float | None
    acquired_area_ha: float | None
    risk_level: str | None = None
    risk_score: float | None = None
    data_source: str


class CompensationSummary(BaseModel):
    assessed_amount_inr: float | None
    paid_amount_inr: float | None
    status: str


class PossessionSummary(BaseModel):
    status: str
    area_ha: float | None


class RRSummary(BaseModel):
    affected_families: int
    displaced_families: int
    rehab_completed: int
    resettled: int


class AcquisitionDetail(BaseModel):
    id: UUID
    case_number: str
    project_id: UUID
    project_code: str
    project_name: str
    parcel_id: UUID
    ulpin: str
    khasra_number: str
    current_stage: str
    status: str
    notified_area_ha: float | None
    acquired_area_ha: float | None
    started_at: datetime | None
    completed_at: datetime | None
    compensation: CompensationSummary | None = None
    possession: PossessionSummary | None = None
    rr: RRSummary | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    data_source: str


class TimelineEvent(BaseModel):
    id: UUID
    from_stage: str | None
    to_stage: str
    occurred_at: datetime
    actor_id: UUID | None
    actor_name: str | None
    remarks: str | None


class TimelineResponse(BaseModel):
    stages: list[str]
    events: list[TimelineEvent]
