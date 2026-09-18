from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    purpose: str
    state_code: str
    district_code: str | None
    area_ha: float | None
    status: str
    current_stage: str | None
    data_source: str


class ProjectDetail(BaseModel):
    id: UUID
    code: str
    name: str
    purpose: str
    requiring_body: str | None
    state_code: str
    district_code: str | None
    estimated_area_ha: float | None
    estimated_compensation_inr: float | None
    start_date: date | None
    expected_end_date: date | None
    status: str
    current_stage: str | None
    parcel_count: int
    case_count: int
    area_notified_ha: float
    area_acquired_ha: float
    compensation_assessed_inr: float
    compensation_paid_inr: float
    affected_families: int
    displaced_families: int
    data_source: str


class ProjectCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=255)
    purpose: str = Field(min_length=2)
    requiring_body: str | None = None
    state_code: str = Field(min_length=2, max_length=2)
    district_code: str | None = None
    estimated_area_ha: float | None = Field(default=None, ge=0)
    estimated_compensation_inr: float | None = Field(default=None, ge=0)
    start_date: date | None = None
    expected_end_date: date | None = None
    status: str = "PLANNED"
    current_stage: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    purpose: str | None = None
    requiring_body: str | None = None
    estimated_area_ha: float | None = Field(default=None, ge=0)
    estimated_compensation_inr: float | None = Field(default=None, ge=0)
    start_date: date | None = None
    expected_end_date: date | None = None
    status: str | None = None
    current_stage: str | None = None
    district_code: str | None = None
