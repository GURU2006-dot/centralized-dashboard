"""Phase 1 database foundation tests. Requires migrated + seeded database."""

from __future__ import annotations

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.models import (
    AcquisitionCase,
    LandParcel,
    Owner,
    ParcelOwner,
    Project,
    Proposal,
    ProposalParcel,
    WorkflowEvent,
    WorkflowStageDefinition,
)

REQUIRED_TABLES = {
    "roles",
    "users",
    "states",
    "districts",
    "workflow_stage_definitions",
    "projects",
    "land_parcels",
    "owners",
    "parcel_owners",
    "proposals",
    "proposal_parcels",
    "acquisition_cases",
    "workflow_events",
    "documents",
    "compensation",
    "affected_families",
    "rehabilitation",
    "resettlement",
    "possession",
    "field_verifications",
    "notifications",
    "alerts",
    "ml_predictions",
    "audit_logs",
}

CASE_STAGES = {
    "SIA",
    "NOTIFICATION",
    "AWARD",
    "COMPENSATION_ASSESSMENT",
    "COMPENSATION_PAID",
    "POSSESSION",
    "REHABILITATION_RESETTLEMENT",
    "COMPLETED",
}


def test_postgis_enabled(session):
    version = session.execute(text("SELECT PostGIS_Version()")).scalar()
    assert version
    assert "3." in version or "2." in version


def test_required_tables_exist(engine):
    names = set(inspect(engine).get_table_names())
    missing = REQUIRED_TABLES - names
    assert not missing, f"missing tables: {missing}"


def test_at_least_80_synthetic_parcels(session):
    n = session.scalar(select(func.count()).select_from(LandParcel))
    assert n >= 80
    sources = session.scalars(select(LandParcel.data_source).distinct()).all()
    assert sources == ["SYNTHETIC"]


def test_parcel_owner_mn(session):
    joins = session.scalar(select(func.count()).select_from(ParcelOwner))
    assert joins >= 80
    joint = session.scalar(
        select(func.count()).select_from(ParcelOwner).where(ParcelOwner.ownership_type == "JOINT")
    )
    assert joint >= 2
    owners = session.scalar(select(func.count()).select_from(Owner))
    assert owners >= 80


def test_project_parcel_relationship(session):
    unassigned = session.scalar(
        select(func.count()).select_from(LandParcel).where(LandParcel.project_id.is_(None))
    )
    assert unassigned == 0
    n_projects = session.scalar(select(func.count()).select_from(Project))
    assert n_projects == 8


def test_proposal_parcel_relationship(session):
    n = session.scalar(select(func.count()).select_from(ProposalParcel))
    assert n >= 80
    statuses = set(session.scalars(select(Proposal.status)).all())
    assert "APPROVED" in statuses
    assert "REJECTED" in statuses or "DRAFT" in statuses


def test_cases_only_for_approved_proposals(session):
    """Proposal approval is authoritative; cases are not a second approval path."""
    rows = session.execute(
        select(AcquisitionCase.id, Proposal.status).join(
            Proposal, AcquisitionCase.proposal_id == Proposal.id
        )
    ).all()
    assert rows
    assert all(status == "APPROVED" for _, status in rows)


def test_acquisition_case_uniqueness(session):
    first = session.scalars(select(AcquisitionCase)).first()
    assert first is not None
    session.add(
        AcquisitionCase(
            case_number="ACQ-DUP-TEST",
            project_id=first.project_id,
            parcel_id=first.parcel_id,
            proposal_id=first.proposal_id,
            current_stage=first.current_stage,
            status="OPEN",
            data_source="SYNTHETIC",
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_workflow_stage_catalogue(session):
    codes = set(session.scalars(select(WorkflowStageDefinition.code)).all())
    assert codes == CASE_STAGES
    # Must not reintroduce proposal-approval as a case stage
    assert "APPROVAL" not in codes
    assert "PROPOSAL" not in codes


def test_workflow_events_exist(session):
    n = session.scalar(select(func.count()).select_from(WorkflowEvent))
    assert n >= 60


def test_workflow_events_append_only(session):
    event = session.scalars(select(WorkflowEvent)).first()
    assert event is not None
    event.remarks = "should fail"
    with pytest.raises(Exception):
        session.flush()
    session.rollback()
    with pytest.raises(Exception):
        session.execute(
            text("DELETE FROM workflow_events WHERE id = :id"),
            {"id": event.id},
        )
        session.flush()
    session.rollback()


def test_geometry_roundtrip(session):
    parcel = session.scalars(select(LandParcel).where(LandParcel.geom.is_not(None))).first()
    assert parcel is not None
    geojson = session.execute(
        text("SELECT ST_AsGeoJSON(geom) FROM land_parcels WHERE id = :id"),
        {"id": parcel.id},
    ).scalar()
    assert geojson
    assert "Polygon" in geojson or "MultiPolygon" in geojson
    n_geom = session.scalar(
        select(func.count()).select_from(LandParcel).where(LandParcel.geom.is_not(None))
    )
    assert n_geom >= 80


def test_data_source_check_rejects_unknown(session):
    parcel = session.scalars(select(LandParcel)).first()
    parcel.data_source = "LIVE_GOVERNMENT"
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_insert_geometry(session):
    wkt = WKTElement(
        "MULTIPOLYGON(((78.0 17.0, 78.001 17.0, 78.001 17.001, 78.0 17.001, 78.0 17.0)))",
        srid=4326,
    )
    row = LandParcel(
        ulpin="SYN99999999999",
        khasra_number="TEST/1",
        village="Synthetic Test",
        tehsil="Synthetic Test",
        state_code="TG",
        district_code="TG-RR",
        area_ha=1.0,
        acquisition_status="NOT_STARTED",
        geom=wkt,
        data_source="SYNTHETIC",
    )
    session.add(row)
    session.flush()
    found = session.scalar(select(LandParcel).where(LandParcel.ulpin == "SYN99999999999"))
    assert found is not None
    session.rollback()
