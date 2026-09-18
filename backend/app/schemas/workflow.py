from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    project_id: UUID
    parcel_ids: list[UUID] = Field(default_factory=list)
    required_area_ha: float = Field(ge=0)
    purpose: str = Field(min_length=2)
    estimated_compensation_inr: float | None = Field(default=None, ge=0)
    affected_families_count: int | None = Field(default=None, ge=0)
    proposed_start: date | None = None
    proposed_end: date | None = None
    proposal_number: str | None = None


class ProposalUpdate(BaseModel):
    required_area_ha: float | None = Field(default=None, ge=0)
    purpose: str | None = None
    estimated_compensation_inr: float | None = Field(default=None, ge=0)
    affected_families_count: int | None = Field(default=None, ge=0)
    proposed_start: date | None = None
    proposed_end: date | None = None
    parcel_ids: list[UUID] | None = None


class RemarksBody(BaseModel):
    remarks: str | None = None


class RejectBody(BaseModel):
    remarks: str = Field(min_length=1)


class TransitionBody(BaseModel):
    to_stage: str = Field(min_length=2)
    remarks: str | None = None


class CompensationCreate(BaseModel):
    acquisition_case_id: UUID
    assessed_amount_inr: float = Field(ge=0)
    paid_amount_inr: float = Field(default=0, ge=0)
    assessment_date: date | None = None
    due_date: date | None = None
    payment_date: date | None = None
    remarks: str | None = None


class CompensationUpdate(BaseModel):
    assessed_amount_inr: float | None = Field(default=None, ge=0)
    paid_amount_inr: float | None = Field(default=None, ge=0)
    assessment_date: date | None = None
    due_date: date | None = None
    payment_date: date | None = None
    status: str | None = None
    remarks: str | None = None


class PossessionCreate(BaseModel):
    acquisition_case_id: UUID
    status: str = "NOT_TAKEN"
    area_ha: float | None = Field(default=None, ge=0)
    taken_at: datetime | None = None
    remarks: str | None = None


class PossessionUpdate(BaseModel):
    status: str | None = None
    area_ha: float | None = Field(default=None, ge=0)
    taken_at: datetime | None = None
    remarks: str | None = None


class RehabCreate(BaseModel):
    family_id: UUID
    package_type: str | None = None
    amount_inr: float | None = Field(default=None, ge=0)
    status: str | None = None
    start_date: date | None = None
    completion_date: date | None = None


class RehabUpdate(BaseModel):
    package_type: str | None = None
    amount_inr: float | None = Field(default=None, ge=0)
    status: str | None = None
    start_date: date | None = None
    completion_date: date | None = None


class ResetCreate(BaseModel):
    family_id: UUID
    site_name: str | None = None
    plot_allotted: str | None = None
    status: str | None = None
    allotted_date: date | None = None
    possession_date: date | None = None


class ResetUpdate(BaseModel):
    site_name: str | None = None
    plot_allotted: str | None = None
    status: str | None = None
    allotted_date: date | None = None
    possession_date: date | None = None


class FamilyCreate(BaseModel):
    project_id: UUID
    parcel_id: UUID | None = None
    family_head_name: str = Field(min_length=2)
    member_count: int = Field(ge=1)
    is_displaced: bool = False
    status: str | None = None


class FamilyUpdate(BaseModel):
    family_head_name: str | None = None
    member_count: int | None = Field(default=None, ge=1)
    is_displaced: bool | None = None
    status: str | None = None
    parcel_id: UUID | None = None


class FieldPatch(BaseModel):
    gps_lat: float | None = None
    gps_lng: float | None = None
    owner_verified: bool | None = None
    land_info_verified: bool | None = None
    documents_verified: bool | None = None
    remarks: str | None = None


class DocumentVerify(BaseModel):
    verification_status: str
    remarks: str | None = None
