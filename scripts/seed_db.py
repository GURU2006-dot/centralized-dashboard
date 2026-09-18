#!/usr/bin/env python3
"""Load SYNTHETIC demonstration data. Not live government land records."""

from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from geoalchemy2 import WKTElement
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AcquisitionCase,
    AffectedFamily,
    Alert,
    AuditLog,
    Compensation,
    District,
    Document,
    FieldVerification,
    LandParcel,
    MLPrediction,
    Notification,
    Owner,
    ParcelOwner,
    Possession,
    Project,
    Proposal,
    ProposalParcel,
    Rehabilitation,
    Resettlement,
    Role,
    State,
    User,
    WorkflowEvent,
    WorkflowStageDefinition,
)

NS = uuid.UUID("26016000-0000-4000-8000-000000000000")
RNG = random.Random(26016)
NOW = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

# bcrypt hash of Demo@1234 (prototype only — not a production secret)
# bcrypt hash of Demo@1234 generated with bcrypt 4.x (prototype only)
DEMO_PASSWORD_HASH = "$2b$12$BOkLLQHCPL512TNpH7t8/uF6BmNUQHUmrVdTVnYg8SwvHFhWEcw6i"

STAGES = [
    ("SIA", "Social Impact Assessment", 1, 60, False),
    ("NOTIFICATION", "Preliminary notification", 2, 30, False),
    ("AWARD", "Award", 3, 21, False),
    ("COMPENSATION_ASSESSMENT", "Compensation assessment", 4, 30, False),
    ("COMPENSATION_PAID", "Compensation paid", 5, 30, False),
    ("POSSESSION", "Possession", 6, 21, False),
    ("REHABILITATION_RESETTLEMENT", "Rehabilitation & Resettlement", 7, 90, False),
    ("COMPLETED", "Completed", 8, 0, True),
]

# Cases are created only after proposal APPROVED; they enter at SIA.
STAGE_SEQUENCE = [s[0] for s in STAGES]

STATES = [
    ("TG", "Telangana", 17.849, 79.287),
    ("MH", "Maharashtra", 19.751, 75.713),
    ("OD", "Odisha", 20.951, 85.098),
]

DISTRICTS = [
    ("TG-RR", "TG", "Rangareddy"),
    ("TG-HYD", "TG", "Hyderabad"),
    ("MH-NGP", "MH", "Nagpur"),
    ("MH-PUN", "MH", "Pune"),
    ("OD-KHO", "OD", "Khordha"),
    ("OD-CTC", "OD", "Cuttack"),
]

DISTRICT_CENTROIDS = {
    "TG-HYD": (17.3850, 78.4867),
    "TG-RR": (17.2543, 78.2850),
    "MH-NGP": (21.1458, 79.0882),
    "MH-PUN": (18.5204, 73.8567),
    "OD-KHO": (20.1820, 85.6180),
    "OD-CTC": (20.4625, 85.8830),
}

PROJECTS_SPEC = [
    # code, name, purpose, body, state, district, status, stage, delayed
    ("NH-TG-044", "NH-44 Hyderabad widening", "National highway widening", "NHAI", "TG", "TG-RR", "ACTIVE", "NOTIFICATION", False),
    ("IR-TG-MM", "Hyderabad Metro Phase-2 depot", "Metro depot and alignment", "HMRL", "TG", "TG-HYD", "DELAYED", "SIA", True),
    ("IR-MH-NGP", "Nagpur–Mumbai Expressway parcel", "Expressway right of way", "MSRDC", "MH", "MH-NGP", "ACTIVE", "AWARD", False),
    ("IR-MH-PUN", "Pune Ring Road Sector C", "Ring road construction", "MSRDC", "MH", "MH-PUN", "ACTIVE", "COMPENSATION_ASSESSMENT", False),
    ("IR-OD-CTC", "Cuttack flood embankment", "Flood protection embankment", "Water Resources Dept.", "OD", "OD-CTC", "ACTIVE", "POSSESSION", False),
    ("IR-OD-KHO", "Bhubaneswar peri-urban corridor", "Urban mobility corridor", "BDA", "OD", "OD-KHO", "ACTIVE", "COMPENSATION_PAID", False),
    ("TH-TG-SEZ", "Maheshwaram industrial node", "Industrial node (proposal pending)", "TSIIC", "TG", "TG-RR", "PLANNED", "SIA", False),
    ("TH-MH-PWR", "Pune transmission corridor", "Power transmission ROW (rejected demo)", "MSETCL", "MH", "MH-PUN", "ON_HOLD", "SIA", False),
]

VILLAGES = {
    "TG-RR": ("Shamshabad", "Maheshwaram", "Kothur"),
    "TG-HYD": ("Uppal", "Gachibowli", "Kukatpally"),
    "MH-NGP": ("Hingna", "Kamptee", "Kalmeshwar"),
    "MH-PUN": ("Haveli", "Mulshi", "Khed"),
    "OD-KHO": ("Jatni", "Balianta", "Balipatna"),
    "OD-CTC": ("Barang", "Kantabada", "Niali"),
}

FIRST_NAMES = [
    "Ramesh", "Sita", "Anil", "Lakshmi", "Prakash", "Meena", "Suresh", "Kavita",
    "Arjun", "Padma", "Venkatesh", "Sunita", "Ibrahim", "Fatima", "Joseph", "Mary",
    "Hari", "Radha", "Gopal", "Nirmala",
]
LAST_NAMES = [
    "Reddy", "Rao", "Naik", "Patil", "Deshmukh", "Sharma", "Das", "Sahu",
    "Mohanty", "Kulkarni", "Singh", "Begum",
]


def uid(name: str) -> uuid.UUID:
    return uuid.uuid5(NS, name)


def ulpin14(n: int) -> str:
    return f"SYN{n:011d}"  # SYN + 11 digits = 14; prefix SYN = synthetic, not DoLR ULPIN


def square_wkt(lat: float, lng: float, half: float = 0.0012) -> str:
    # WKT is lon lat
    ring = [
        (lng - half, lat - half),
        (lng + half, lat - half),
        (lng + half, lat + half),
        (lng - half, lat + half),
        (lng - half, lat - half),
    ]
    coords = ", ".join(f"{x:.6f} {y:.6f}" for x, y in ring)
    return f"MULTIPOLYGON((({coords})))"


def geojson_polygon(lat: float, lng: float, half: float = 0.0012) -> dict:
    ring = [
        [lng - half, lat - half],
        [lng + half, lat - half],
        [lng + half, lat + half],
        [lng - half, lat + half],
        [lng - half, lat - half],
    ]
    return {"type": "MultiPolygon", "coordinates": [[ring]]}


def seed_catalogue(session) -> None:
    session.add_all(
        [
            WorkflowStageDefinition(
                code=code,
                name=name,
                sequence_order=order,
                expected_duration_days=days,
                is_terminal=terminal,
                description=(
                    "Post-approval acquisition lifecycle stage. "
                    "Proposal approval is recorded on proposals.status, not here."
                ),
            )
            for code, name, order, days, terminal in STAGES
        ]
    )
    session.add_all(
        [
            State(code=c, name=n, centroid_lat=lat, centroid_lng=lng)
            for c, n, lat, lng in STATES
        ]
    )
    session.add_all(
        [District(code=c, state_code=s, name=n) for c, s, n in DISTRICTS]
    )


def seed_users(session) -> dict[str, User]:
    roles = {
        "ADMIN": Role(
            id=uid("role:ADMIN"),
            code="ADMIN",
            name="Administrator",
            description="National administration",
        ),
        "ACQUISITION_OFFICER": Role(
            id=uid("role:ACQ"),
            code="ACQUISITION_OFFICER",
            name="Acquisition Officer",
            description="Creates proposals and manages cases",
        ),
        "APPROVING_AUTHORITY": Role(
            id=uid("role:APPR"),
            code="APPROVING_AUTHORITY",
            name="Approving Authority",
            description="Authoritative proposal approve/reject only",
        ),
        "FIELD_OFFICER": Role(
            id=uid("role:FIELD"),
            code="FIELD_OFFICER",
            name="Field Officer",
            description="Field verification",
        ),
    }
    session.add_all(roles.values())
    users = {
        "admin": User(
            id=uid("user:admin"),
            email="admin@demo.local",
            hashed_password=DEMO_PASSWORD_HASH,
            full_name="National Admin",
            role_id=roles["ADMIN"].id,
            is_active=True,
        ),
        "officer": User(
            id=uid("user:officer"),
            email="officer@demo.local",
            hashed_password=DEMO_PASSWORD_HASH,
            full_name="Telangana Acquisition Officer",
            role_id=roles["ACQUISITION_OFFICER"].id,
            state_code="TG",
            is_active=True,
        ),
        "approver": User(
            id=uid("user:approver"),
            email="approver@demo.local",
            hashed_password=DEMO_PASSWORD_HASH,
            full_name="Approving Authority",
            role_id=roles["APPROVING_AUTHORITY"].id,
            is_active=True,
        ),
        "field": User(
            id=uid("user:field"),
            email="field@demo.local",
            hashed_password=DEMO_PASSWORD_HASH,
            full_name="Rangareddy Field Officer",
            role_id=roles["FIELD_OFFICER"].id,
            state_code="TG",
            district_code="TG-RR",
            is_active=True,
        ),
    }
    session.add_all(users.values())
    return users


def seed_projects(session, users) -> list[Project]:
    projects = []
    for spec in PROJECTS_SPEC:
        code, name, purpose, body, state, district, status, stage, _delayed = spec
        p = Project(
            id=uid(f"project:{code}"),
            code=code,
            name=name,
            purpose=purpose,
            requiring_body=body,
            state_code=state,
            district_code=district,
            estimated_area_ha=round(RNG.uniform(40, 180), 4),
            estimated_compensation_inr=round(RNG.uniform(8e7, 6e8), 2),
            start_date=date(2025, 4, 1),
            expected_end_date=date(2027, 3, 31),
            status=status,
            current_stage=stage,
            created_by=users["officer"].id,
            data_source="SYNTHETIC",
        )
        projects.append(p)
    session.add_all(projects)
    return projects


def seed_parcels_and_owners(session, projects) -> list[LandParcel]:
    owners: list[Owner] = []
    for i in range(1, 96):
        fn = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
        ln = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
        owners.append(
            Owner(
                id=uid(f"owner:{i}"),
                name=f"{fn} {ln}",
                father_or_spouse_name=f"{LAST_NAMES[i % len(LAST_NAMES)]} {ln}",
                id_type="AADHAAR_SYNTH",
                id_number=f"SYNTH-ID-{i:06d}",
                phone=f"90000{i:05d}"[:10],
                address=f"Synthetic house {i}, Demo village (NOT a real address)",
                data_source="SYNTHETIC",
            )
        )
    session.add_all(owners)

    parcels: list[LandParcel] = []
    ownerships: list[ParcelOwner] = []
    n = 0
    for p_idx, project in enumerate(projects):
        base_lat, base_lng = DISTRICT_CENTROIDS[project.district_code]
        villages = VILLAGES[project.district_code]
        for j in range(10):
            n += 1
            lat = base_lat + ((j % 5) - 2) * 0.012 + p_idx * 0.0003
            lng = base_lng + ((j // 5) - 1) * 0.014 + j * 0.0011
            village = villages[j % len(villages)]
            wkt = square_wkt(lat, lng)
            gj = geojson_polygon(lat, lng)
            parcel = LandParcel(
                id=uid(f"parcel:{n}"),
                ulpin=ulpin14(n),
                khasra_number=f"{(j % 20) + 1}/{n}",
                village=village,
                tehsil=village,
                state_code=project.state_code,
                district_code=project.district_code,
                area_ha=round(RNG.uniform(0.4, 3.8), 4),
                project_id=project.id,
                acquisition_status="NOT_STARTED",
                current_stage=None,
                centroid=WKTElement(f"POINT({lng:.6f} {lat:.6f})", srid=4326),
                geom=WKTElement(wkt, srid=4326),
                geometry_geojson=gj,
                data_source="SYNTHETIC",
            )
            parcels.append(parcel)
            primary = owners[n - 1]
            if j % 3 == 0:
                second = owners[n]
                ownerships.append(
                    ParcelOwner(
                        parcel_id=parcel.id,
                        owner_id=primary.id,
                        ownership_share_pct=60,
                        ownership_type="JOINT",
                    )
                )
                ownerships.append(
                    ParcelOwner(
                        parcel_id=parcel.id,
                        owner_id=second.id,
                        ownership_share_pct=40,
                        ownership_type="JOINT",
                    )
                )
            else:
                ownerships.append(
                    ParcelOwner(
                        parcel_id=parcel.id,
                        owner_id=primary.id,
                        ownership_share_pct=100,
                        ownership_type="SOLE",
                    )
                )
    session.add_all(parcels)
    session.add_all(ownerships)
    return parcels


def seed_proposals(session, projects, parcels, users) -> list[Proposal]:
    """Authoritative approval is proposals.status. Cases exist only for APPROVED."""
    grouped = {p.id: [] for p in projects}
    for parcel in parcels:
        grouped[parcel.project_id].append(parcel)

    specs = [
        (0, "PROP-2026-001", "APPROVED", "NH widening — approved"),
        (1, "PROP-2026-002", "APPROVED", "Metro depot — approved (delayed)"),
        (2, "PROP-2026-003", "APPROVED", "Expressway — approved"),
        (3, "PROP-2026-004", "APPROVED", "Ring road — approved"),
        (4, "PROP-2026-005", "APPROVED", "Embankment — approved"),
        (5, "PROP-2026-006", "APPROVED", "Peri-urban corridor — approved"),
        (6, "PROP-2026-007", "DRAFT", "Industrial node — still draft"),
        (7, "PROP-2026-008", "REJECTED", "Transmission corridor — rejected"),
    ]
    proposals = []
    links = []
    for idx, number, status, purpose in specs:
        project = projects[idx]
        plist = grouped[project.id]
        submitted = status != "DRAFT"
        approved = status == "APPROVED"
        rejected = status == "REJECTED"
        pr = Proposal(
            id=uid(f"proposal:{number}"),
            proposal_number=number,
            project_id=project.id,
            required_area_ha=sum(float(x.area_ha) for x in plist),
            purpose=purpose,
            estimated_compensation_inr=project.estimated_compensation_inr,
            affected_families_count=8 + idx * 3,
            proposed_start=date(2026, 1, 15),
            proposed_end=date(2027, 6, 30),
            status=status,
            submitted_by=users["officer"].id if submitted else None,
            submitted_at=NOW - timedelta(days=80 - idx) if submitted else None,
            reviewed_by=users["approver"].id if approved or rejected else None,
            reviewed_at=NOW - timedelta(days=60 - idx) if approved or rejected else None,
            review_remarks=(
                "Approved for acquisition workflow."
                if approved
                else ("Insufficient alignment with master plan." if rejected else None)
            ),
            data_source="SYNTHETIC",
        )
        proposals.append(pr)
        for parcel in plist:
            links.append(ProposalParcel(proposal_id=pr.id, parcel_id=parcel.id))
    session.add_all(proposals)
    session.add_all(links)
    return proposals


def _history_for_stage(stage: str) -> list[str]:
    idx = STAGE_SEQUENCE.index(stage)
    return STAGE_SEQUENCE[: idx + 1]


def seed_cases(session, projects, parcels, proposals, users) -> list[AcquisitionCase]:
    proposal_by_project = {pr.project_id: pr for pr in proposals}
    approved_project_ids = {pr.project_id for pr in proposals if pr.status == "APPROVED"}

    # Distribute 60 cases (projects 0-5) across post-approval stages.
    stage_plan = (
        ["SIA"] * 10
        + ["NOTIFICATION"] * 10
        + ["AWARD"] * 8
        + ["COMPENSATION_ASSESSMENT"] * 8
        + ["COMPENSATION_PAID"] * 8
        + ["POSSESSION"] * 6
        + ["REHABILITATION_RESETTLEMENT"] * 6
        + ["COMPLETED"] * 4
    )
    assert len(stage_plan) == 60

    eligible = [p for p in parcels if p.project_id in approved_project_ids]
    eligible.sort(key=lambda p: p.ulpin)
    cases = []
    events = []
    for i, parcel in enumerate(eligible):
        stage = stage_plan[i]
        history = _history_for_stage(stage)
        project = next(p for p in projects if p.id == parcel.project_id)
        proposal = proposal_by_project[project.id]
        started = NOW - timedelta(days=90 - i)
        case = AcquisitionCase(
            id=uid(f"case:{parcel.ulpin}"),
            case_number=f"ACQ-2026-{i + 1:04d}",
            project_id=project.id,
            parcel_id=parcel.id,
            proposal_id=proposal.id,
            current_stage=stage,
            status="CLOSED" if stage == "COMPLETED" else "OPEN",
            notified_area_ha=parcel.area_ha if STAGE_SEQUENCE.index(stage) >= 1 else None,
            acquired_area_ha=parcel.area_ha if STAGE_SEQUENCE.index(stage) >= 5 else None,
            stage_entered_at=NOW - timedelta(days=7 + (i % 11)),
            expected_stage_exit_at=NOW + timedelta(days=14 - (i % 20)),
            started_at=started,
            completed_at=NOW - timedelta(days=2) if stage == "COMPLETED" else None,
            data_source="SYNTHETIC",
        )
        cases.append(case)
        parcel.current_stage = stage
        if stage == "COMPLETED":
            parcel.acquisition_status = "ACQUIRED"
        elif stage in ("POSSESSION", "REHABILITATION_RESETTLEMENT"):
            parcel.acquisition_status = "ACQUIRED"
        elif i % 17 == 0:
            parcel.acquisition_status = "DISPUTED"
        else:
            parcel.acquisition_status = "IN_PROCESS"

        prev = None
        for step_i, to_stage in enumerate(history):
            events.append(
                WorkflowEvent(
                    id=uid(f"event:{parcel.ulpin}:{to_stage}"),
                    acquisition_case_id=case.id,
                    from_stage=prev,
                    to_stage=to_stage,
                    occurred_at=started + timedelta(days=step_i * 8),
                    actor_user_id=users["officer"].id,
                    remarks=f"Synthetic transition into {to_stage}",
                    extra_metadata={"synthetic": True, "source": "seed"},
                )
            )
            prev = to_stage
    session.add_all(cases)
    session.flush()
    session.add_all(events)
    return cases


def seed_money_rr_field(session, cases, parcels, projects, users) -> None:
    comps = []
    poss = []
    docs = []
    for i, case in enumerate(cases):
        stage_idx = STAGE_SEQUENCE.index(case.current_stage)
        parcel = next(p for p in parcels if p.id == case.parcel_id)
        if stage_idx >= 3:
            assessed = round(float(parcel.area_ha) * 4_500_000, 2)
            if case.current_stage in ("COMPENSATION_PAID", "POSSESSION", "REHABILITATION_RESETTLEMENT", "COMPLETED"):
                status = "PAID"
                paid = assessed
            elif case.current_stage == "COMPENSATION_ASSESSMENT":
                status = "ASSESSED"
                paid = 0
            else:
                status = "PARTIAL"
                paid = round(assessed * 0.4, 2)
            comps.append(
                Compensation(
                    id=uid(f"comp:{case.case_number}"),
                    acquisition_case_id=case.id,
                    assessed_amount_inr=assessed,
                    paid_amount_inr=paid,
                    status=status,
                    assessment_date=date(2026, 5, 1),
                    due_date=date(2026, 8, 31),
                    payment_date=date(2026, 7, 15) if status == "PAID" else None,
                    remarks="Synthetic compensation figures",
                    data_source="SYNTHETIC",
                )
            )
        if stage_idx >= 5:
            poss.append(
                Possession(
                    id=uid(f"poss:{case.case_number}"),
                    acquisition_case_id=case.id,
                    status="TAKEN" if stage_idx >= 6 else "PARTIAL",
                    area_ha=parcel.area_ha,
                    taken_at=NOW - timedelta(days=10) if stage_idx >= 6 else None,
                    taken_by=users["officer"].id,
                    remarks="Synthetic possession record",
                    data_source="SYNTHETIC",
                )
            )
        if i % 2 == 0:
            docs.append(
                Document(
                    id=uid(f"doc:{case.case_number}"),
                    public_id=f"DOC{i + 1:05d}",
                    name=f"Synthetic land record {parcel.ulpin}",
                    doc_type="LAND_RECORD",
                    project_id=case.project_id,
                    parcel_id=case.parcel_id,
                    acquisition_case_id=case.id,
                    storage_path=f"synthetic://documents/{case.case_number}/land-record.pdf",
                    mime_type="application/pdf",
                    byte_size=12000,
                    uploaded_by=users["officer"].id,
                    verification_status="VERIFIED" if i % 4 else "PENDING",
                    remarks="Placeholder file — not a government extract",
                    data_source="SYNTHETIC",
                )
            )
    session.add_all(comps)
    session.add_all(poss)
    session.add_all(docs)

    families = []
    rehabs = []
    resets = []
    fam_n = 0
    for p_i, project in enumerate(projects[:6]):
        for k in range(6 + p_i):
            fam_n += 1
            displaced = fam_n % 3 == 0
            fam = AffectedFamily(
                id=uid(f"fam:{fam_n}"),
                project_id=project.id,
                parcel_id=None,
                family_head_name=f"{FIRST_NAMES[fam_n % len(FIRST_NAMES)]} {LAST_NAMES[fam_n % len(LAST_NAMES)]}",
                member_count=2 + (fam_n % 5),
                is_displaced=displaced,
                contact=None,  # not used as live PII
                status="RESETTLED" if displaced and fam_n % 2 == 0 else "IDENTIFIED",
                data_source="SYNTHETIC",
            )
            families.append(fam)
            if displaced:
                rehabs.append(
                    Rehabilitation(
                        id=uid(f"rehab:{fam_n}"),
                        family_id=fam.id,
                        project_id=project.id,
                        package_type="LIVELIHOOD",
                        amount_inr=250000,
                        status="COMPLETED" if fam.status == "RESETTLED" else "IN_PROGRESS",
                        start_date=date(2026, 2, 1),
                        data_source="SYNTHETIC",
                    )
                )
                resets.append(
                    Resettlement(
                        id=uid(f"reset:{fam_n}"),
                        family_id=fam.id,
                        project_id=project.id,
                        site_name=f"Synthetic R&R site {project.code}",
                        plot_allotted=f"P-{fam_n:03d}",
                        status="POSSESSED" if fam.status == "RESETTLED" else "ALLOTTED",
                        allotted_date=date(2026, 3, 1),
                        data_source="SYNTHETIC",
                    )
                )
    session.add_all(families)
    session.add_all(rehabs)
    session.add_all(resets)

    field_rows = []
    tg_parcels = [p for p in parcels if p.district_code == "TG-RR"][:8]
    for i, parcel in enumerate(tg_parcels):
        case = next((c for c in cases if c.parcel_id == parcel.id), None)
        field_rows.append(
            FieldVerification(
                id=uid(f"field:{i}"),
                parcel_id=parcel.id,
                acquisition_case_id=case.id if case else None,
                assigned_to=users["field"].id,
                status="SUBMITTED" if i < 3 else "ASSIGNED",
                gps_lat=17.25 + i * 0.001 if i < 3 else None,
                gps_lng=78.28 + i * 0.001 if i < 3 else None,
                owner_verified=True if i < 3 else None,
                land_info_verified=True if i < 3 else None,
                documents_verified=i < 2 if i < 3 else None,
                remarks="Synthetic field task",
                submitted_at=NOW - timedelta(days=1) if i < 3 else None,
                submitted_by=users["field"].id if i < 3 else None,
                data_source="SYNTHETIC",
            )
        )
    session.add_all(field_rows)


def seed_alerts_ml_audit(session, cases, projects, users) -> None:
    officer = users["officer"]
    alerts = []
    for i, case in enumerate(cases[:12]):
        rules = [
            ("STAGE_OVERRUN", "DELAY", "HIGH", "Stage duration exceeds expected days (synthetic)."),
            ("ML_HIGH_RISK", "ML", "HIGH", "Model risk score is HIGH (synthetic model)."),
            ("COMPENSATION_DUE", "COMPENSATION", "MEDIUM", "Compensation due date approaching (synthetic)."),
            ("FIELD_INCOMPLETE", "FIELD", "LOW", "Field verification still assigned (synthetic)."),
            ("APPROVAL_PENDING", "PROPOSAL", "MEDIUM", "Unrelated demo: draft proposal waiting — not a case approval."),
        ]
        rule_code, alert_type, sev, msg = rules[i % len(rules)]
        alerts.append(
            Alert(
                id=uid(f"alert:{i}"),
                rule_code=rule_code,
                alert_type=alert_type,
                severity=sev,
                project_id=case.project_id,
                parcel_id=case.parcel_id,
                acquisition_case_id=case.id,
                message=msg,
                recipient_user_id=officer.id,
                is_read=i % 3 == 0,
                extra_metadata={"synthetic": True},
                data_source="SYNTHETIC",
            )
        )
    session.add_all(alerts)
    session.add_all(
        [
            Notification(
                id=uid(f"note:{i}"),
                user_id=officer.id,
                title="Synthetic notification",
                body="Demo in-app notice. Not a government SMS.",
                channel="IN_APP",
                related_type="acquisition_case",
                related_id=str(cases[i].id),
                is_read=False,
                data_source="SYNTHETIC",
            )
            for i in range(8)
        ]
    )

    preds = []
    for i, case in enumerate(cases[:24]):
        # risk_score is a model score, not a calibrated P(delay)
        score = round(0.12 + (i % 10) * 0.08, 4)
        if score > 0.66:
            level = "HIGH"
        elif score > 0.33:
            level = "MEDIUM"
        else:
            level = "LOW"
        preds.append(
            MLPrediction(
                id=uid(f"ml:{i}"),
                acquisition_case_id=case.id,
                project_id=case.project_id,
                risk_level=level,
                risk_score=score,
                features={
                    "sia_duration_days": 10 + i,
                    "approval_delay_days": 0,
                    "document_issue_count": i % 4,
                    "dispute_count": 1 if i % 7 == 0 else 0,
                    "affected_family_count": 5,
                    "owner_count": 1,
                    "compensation_pending_days": i * 2,
                    "project_area_ha": 80,
                    "current_stage_index": STAGE_SEQUENCE.index(case.current_stage) + 1,
                    "previous_processing_delay_days": i,
                    "disclaimer": "Features derived from SYNTHETIC seed rows",
                },
                model_version="rf-delay-v1",
                trained_on="SYNTHETIC",
                predicted_by=users["admin"].id,
            )
        )
    session.add_all(preds)

    session.add_all(
        [
            AuditLog(
                user_id=users["approver"].id,
                action="PROPOSAL_APPROVED",
                entity_type="proposal",
                entity_id=str(uid("proposal:PROP-2026-001")),
                extra_metadata={"synthetic": True, "note": "Authoritative approval action"},
            ),
            AuditLog(
                user_id=users["approver"].id,
                action="PROPOSAL_REJECTED",
                entity_type="proposal",
                entity_id=str(uid("proposal:PROP-2026-008")),
                extra_metadata={"synthetic": True},
            ),
            AuditLog(
                user_id=users["officer"].id,
                action="WORKFLOW_STAGE_CHANGED",
                entity_type="acquisition_case",
                entity_id=str(cases[0].id),
                extra_metadata={"synthetic": True, "to_stage": cases[0].current_stage},
            ),
        ]
    )


def write_geojson_sidecar(session) -> None:
    """Optional file copy of synthetic parcel polygons for GIS tooling."""
    rows = session.execute(
        select(LandParcel.ulpin, LandParcel.geometry_geojson, LandParcel.khasra_number)
    ).all()
    fc = {
        "type": "FeatureCollection",
        "comment": "SYNTHETIC demonstration geometries. Not live cadastral data.",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "ulpin": ulpin_,
                    "khasra_number": khasra,
                    "data_source": "SYNTHETIC",
                },
                "geometry": gj,
            }
            for ulpin_, gj, khasra in rows
            if gj
        ],
    }
    out = ROOT / "data" / "geo" / "parcels.geojson"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fc))


def already_seeded(session) -> bool:
    n = session.scalar(select(func.count()).select_from(LandParcel))
    return bool(n and n > 0)


def run() -> dict[str, int]:
    session = SessionLocal()
    try:
        if already_seeded(session):
            counts = _counts(session)
            print("Database already seeded. Counts:", counts)
            return counts
        seed_catalogue(session)
        users = seed_users(session)
        session.flush()
        projects = seed_projects(session, users)
        session.flush()
        parcels = seed_parcels_and_owners(session, projects)
        session.flush()
        proposals = seed_proposals(session, projects, parcels, users)
        session.flush()
        cases = seed_cases(session, projects, parcels, proposals, users)
        session.flush()
        seed_money_rr_field(session, cases, parcels, projects, users)
        seed_alerts_ml_audit(session, cases, projects, users)
        session.commit()
        write_geojson_sidecar(session)
        counts = _counts(session)
        print("Seed complete (all data_source=SYNTHETIC). Counts:", counts)
        return counts
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _counts(session) -> dict[str, int]:
    tables = {
        "roles": Role,
        "users": User,
        "states": State,
        "districts": District,
        "workflow_stage_definitions": WorkflowStageDefinition,
        "projects": Project,
        "land_parcels": LandParcel,
        "owners": Owner,
        "parcel_owners": ParcelOwner,
        "proposals": Proposal,
        "proposal_parcels": ProposalParcel,
        "acquisition_cases": AcquisitionCase,
        "workflow_events": WorkflowEvent,
        "documents": Document,
        "compensation": Compensation,
        "affected_families": AffectedFamily,
        "rehabilitation": Rehabilitation,
        "resettlement": Resettlement,
        "possession": Possession,
        "field_verifications": FieldVerification,
        "notifications": Notification,
        "alerts": Alert,
        "ml_predictions": MLPrediction,
        "audit_logs": AuditLog,
    }
    return {
        name: session.scalar(select(func.count()).select_from(model)) or 0
        for name, model in tables.items()
    }


if __name__ == "__main__":
    run()
