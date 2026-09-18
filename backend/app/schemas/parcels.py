from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OwnerSummary(BaseModel):
    """Non-sensitive ownership fields only. No id_number, phone, or address."""

    name: str
    ownership_type: str
    share_pct: float | None = None


class ProjectRef(BaseModel):
    id: UUID
    code: str
    name: str


class ParcelListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ulpin: str
    khasra_number: str
    village: str | None
    tehsil: str | None
    state_code: str
    district_code: str
    area_ha: float
    project_id: UUID | None
    project_code: str | None = None
    acquisition_status: str
    current_stage: str | None
    data_source: str
    owner_count: int = 0


class ParcelGeometry(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class ParcelDetail(BaseModel):
    id: UUID
    ulpin: str
    khasra_number: str
    village: str | None
    tehsil: str | None
    state_code: str
    district_code: str
    area_ha: float
    project: ProjectRef | None
    acquisition_status: str
    current_stage: str | None
    owners: list[OwnerSummary]
    location: dict[str, float] | None = None
    geometry: ParcelGeometry | None = None
    data_source: str
