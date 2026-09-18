from __future__ import annotations

from pydantic import BaseModel, Field


class DashboardKpis(BaseModel):
    total_projects: int
    area_notified_ha: float
    area_acquired_ha: float
    compensation_assessed_inr: float
    compensation_paid_inr: float
    affected_families: int
    displaced_families: int
    rr_progress: dict
    projects_at_risk: int
    delayed_projects: int


class StageCount(BaseModel):
    stage: str
    count: int


class StateProgress(BaseModel):
    state_code: str
    projects: int
    area_notified_ha: float
    area_acquired_ha: float


class CompensationChartRow(BaseModel):
    project_id: str
    project_code: str
    assessed_inr: float
    paid_inr: float


class RRStatusCount(BaseModel):
    status: str
    count: int


class RiskCount(BaseModel):
    risk_level: str
    count: int


class DashboardCharts(BaseModel):
    stage_distribution: list[StageCount] = Field(default_factory=list)
    state_wise_progress: list[StateProgress] = Field(default_factory=list)
    compensation: list[CompensationChartRow] = Field(default_factory=list)
    rr_status: list[RRStatusCount] = Field(default_factory=list)
    risk: list[RiskCount] = Field(default_factory=list)


class FilterOption(BaseModel):
    code: str
    name: str


class DashboardFilters(BaseModel):
    states: list[FilterOption]
    districts: list[FilterOption]
    projects: list[FilterOption]
    stages: list[FilterOption]
    statuses: list[FilterOption]
