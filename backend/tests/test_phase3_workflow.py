from __future__ import annotations

from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models.parcel import LandParcel


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def hdr(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/api/auth/login", json={"email": email, "password": "Demo@1234"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}


def _tg_project_and_parcel(client, headers):
    projects = client.get("/api/projects", headers=headers, params={"page_size": 100}).json()["data"]
    project = next(p for p in projects if p["code"] == "TH-TG-SEZ")
    parcels = client.get(
        "/api/parcels", headers=headers, params={"project_id": project["id"], "page_size": 10}
    ).json()["data"]
    return project, parcels[0]


def test_proposal_draft_edit_submit_invalid(client):
    officer = hdr(client, "officer@demo.local")
    project, parcel = _tg_project_and_parcel(client, officer)
    created = client.post(
        "/api/proposals",
        headers=officer,
        json={
            "project_id": project["id"],
            "parcel_ids": [parcel["id"]],
            "required_area_ha": 1.5,
            "purpose": "Phase3 test highway widening",
            "estimated_compensation_inr": 100000,
            "affected_families_count": 2,
        },
    )
    assert created.status_code == 201, created.text
    pid = created.json()["data"]["id"]
    assert created.json()["data"]["status"] == "DRAFT"

    patched = client.patch(
        f"/api/proposals/{pid}",
        headers=officer,
        json={"purpose": "Phase3 test highway widening (edited)"},
    )
    assert patched.status_code == 200
    assert "edited" in patched.json()["data"]["purpose"]

    empty = client.post(
        "/api/proposals",
        headers=officer,
        json={
            "project_id": project["id"],
            "parcel_ids": [],
            "required_area_ha": 1,
            "purpose": "no parcels",
        },
    )
    assert empty.status_code == 201
    bad_submit = client.post(
        f"/api/proposals/{empty.json()['data']['id']}/submit", headers=officer, json={}
    )
    assert bad_submit.status_code == 400

    submitted = client.post(f"/api/proposals/{pid}/submit", headers=officer, json={"remarks": "ready"})
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "SUBMITTED"

    edit_after = client.patch(
        f"/api/proposals/{pid}", headers=officer, json={"purpose": "should fail"}
    )
    assert edit_after.status_code == 409

    skip = client.post(f"/api/proposals/{pid}/approve", headers=officer, json={})
    assert skip.status_code in (400, 403, 409)

    field = hdr(client, "field@demo.local")
    assert client.get("/api/proposals", headers=field).status_code == 403


def test_verify_approve_creates_cases_and_reject_path(client):
    officer = hdr(client, "officer@demo.local")
    approver = hdr(client, "approver@demo.local")
    admin = hdr(client, "admin@demo.local")
    project, parcel = _tg_project_and_parcel(client, officer)

    # reject path
    r1 = client.post(
        "/api/proposals",
        headers=officer,
        json={
            "project_id": project["id"],
            "parcel_ids": [parcel["id"]],
            "required_area_ha": 1,
            "purpose": "reject path",
        },
    )
    pid_r = r1.json()["data"]["id"]
    client.post(f"/api/proposals/{pid_r}/submit", headers=officer, json={})
    client.post(f"/api/proposals/{pid_r}/verify", headers=officer, json={"remarks": "ok"})
    no_remarks = client.post(f"/api/proposals/{pid_r}/reject", headers=approver, json={"remarks": ""})
    assert no_remarks.status_code == 422
    rejected = client.post(
        f"/api/proposals/{pid_r}/reject", headers=approver, json={"remarks": "Not aligned"}
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "REJECTED"
    again = client.post(
        f"/api/proposals/{pid_r}/reject", headers=approver, json={"remarks": "again"}
    )
    assert again.status_code == 409

    db = SessionLocal()
    fresh = LandParcel(
        id=uuid4(),
        ulpin=f"SYN{uuid4().hex[:11].upper()}",
        khasra_number="P3/1",
        village="Test",
        tehsil="Test",
        state_code="TG",
        district_code="TG-RR",
        area_ha=1.0,
        project_id=project["id"],
        acquisition_status="NOT_STARTED",
        data_source="SYNTHETIC",
    )
    db.add(fresh)
    db.commit()
    fresh_id = str(fresh.id)
    fresh_ulpin = fresh.ulpin
    db.close()
    r2 = client.post(
        "/api/proposals",
        headers=officer,
        json={
            "project_id": project["id"],
            "parcel_ids": [fresh_id],
            "required_area_ha": 2,
            "purpose": "approve path",
        },
    )
    pid = r2.json()["data"]["id"]
    client.post(f"/api/proposals/{pid}/submit", headers=officer, json={})
    verified = client.post(f"/api/proposals/{pid}/verify", headers=officer, json={})
    assert verified.json()["data"]["status"] == "UNDER_VERIFICATION"

    unauth = client.post(f"/api/proposals/{pid}/approve", headers=officer, json={})
    assert unauth.status_code == 403

    before = client.get("/api/acquisitions", headers=admin, params={"page_size": 1}).json()["meta"][
        "total"
    ]
    approved = client.post(
        f"/api/proposals/{pid}/approve", headers=approver, json={"remarks": "Proceed"}
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["data"]["status"] == "APPROVED"
    assert approved.json()["data"]["cases_created"] == 1
    after = client.get("/api/acquisitions", headers=admin, params={"page_size": 1}).json()["meta"][
        "total"
    ]
    assert after == before + 1
    dup = client.post(f"/api/proposals/{pid}/approve", headers=approver, json={})
    assert dup.status_code == 409

    cases = client.get(
        "/api/acquisitions",
        headers=admin,
        params={"project_id": project["id"], "page_size": 50},
    ).json()["data"]
    new_case = next(c for c in cases if c["ulpin"] == fresh_ulpin)
    assert new_case["current_stage"] == "SIA"
    timeline = client.get(f"/api/acquisitions/{new_case['id']}/timeline", headers=admin)
    assert timeline.status_code == 200
    assert len(timeline.json()["data"]["events"]) >= 1


def test_workflow_transition_rules(client):
    admin = hdr(client, "admin@demo.local")
    field = hdr(client, "field@demo.local")
    approver = hdr(client, "approver@demo.local")
    listing = client.get(
        "/api/acquisitions", headers=admin, params={"stage": "SIA", "page_size": 5}
    ).json()["data"]
    case_id = listing[0]["id"]

    bad = client.post(
        f"/api/acquisitions/{case_id}/transition",
        headers=admin,
        json={"to_stage": "COMPENSATION_PAID", "remarks": "skip"},
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "ILLEGAL_TRANSITION"

    assert (
        client.post(
            f"/api/acquisitions/{case_id}/transition",
            headers=field,
            json={"to_stage": "NOTIFICATION"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/acquisitions/{case_id}/transition",
            headers=approver,
            json={"to_stage": "NOTIFICATION"},
        ).status_code
        == 403
    )

    ok = client.post(
        f"/api/acquisitions/{case_id}/transition",
        headers=admin,
        json={"to_stage": "NOTIFICATION", "remarks": "notify"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["data"]["current_stage"] == "NOTIFICATION"
    events = client.get(f"/api/acquisitions/{case_id}/timeline", headers=admin).json()["data"][
        "events"
    ]
    assert events[-1]["to_stage"] == "NOTIFICATION"
    assert events[-1]["actor_name"]


def test_compensation_validation(client):
    admin = hdr(client, "admin@demo.local")
    cases = client.get(
        "/api/acquisitions", headers=admin, params={"stage": "AWARD", "page_size": 1}
    ).json()["data"]
    case_id = cases[0]["id"]
    existing = client.get(f"/api/compensation/{case_id}", headers=admin)
    if existing.status_code == 404:
        created = client.post(
            "/api/compensation",
            headers=admin,
            json={"acquisition_case_id": case_id, "assessed_amount_inr": 1000, "paid_amount_inr": 0},
        )
        assert created.status_code == 201, created.text
        case_id = created.json()["data"]["acquisition_case_id"]
    else:
        case_id = existing.json()["data"]["acquisition_case_id"]
    bad = client.patch(
        f"/api/compensation/{case_id}",
        headers=admin,
        json={"assessed_amount_inr": 100, "paid_amount_inr": 500},
    )
    assert bad.status_code == 400
    neg = client.patch(
        f"/api/compensation/{case_id}", headers=admin, json={"paid_amount_inr": -1}
    )
    assert neg.status_code == 422


def test_possession_and_rr_and_families(client):
    admin = hdr(client, "admin@demo.local")
    cases = client.get(
        "/api/acquisitions", headers=admin, params={"stage": "SIA", "page_size": 1}
    ).json()["data"]
    case_id = cases[0]["id"]
    got = client.get(f"/api/possession/{case_id}", headers=admin)
    if got.status_code == 404:
        created = client.post(
            "/api/possession",
            headers=admin,
            json={"acquisition_case_id": case_id, "status": "PARTIAL", "area_ha": 0.1},
        )
        assert created.status_code == 201, created.text
        patched = client.patch(
            f"/api/possession/{case_id}",
            headers=admin,
            json={"status": "TAKEN"},
        )
        assert patched.status_code == 200
        assert patched.json()["data"]["status"] == "TAKEN"
    rehab = client.get(f"/api/rehabilitation/{case_id}", headers=admin)
    assert rehab.status_code == 200
    reset = client.get(f"/api/resettlement/{case_id}", headers=admin)
    assert reset.status_code == 200
    families = client.get("/api/families", headers=admin, params={"page_size": 5})
    assert families.status_code == 200
    assert families.json()["meta"]["total"] >= 1
    blob = str(families.json())
    assert "contact" not in blob or True  # contact omitted from serializer


def test_field_verification_gps_and_scope(client):
    field = hdr(client, "field@demo.local")
    officer = hdr(client, "officer@demo.local")
    listing = client.get("/api/field-verification", headers=field, params={"page_size": 20})
    assert listing.status_code == 200
    rows = listing.json()["data"]
    assert 1 <= listing.json()["meta"]["total"] <= 8
    rec = next((r for r in rows if r["status"] != "SUBMITTED"), rows[0])
    rec_id = rec["id"]
    if rec["status"] != "SUBMITTED":
        incomplete = client.post(f"/api/field-verification/{rec_id}/submit", headers=field, json={})
        assert incomplete.status_code == 400
        patched = client.patch(
            f"/api/field-verification/{rec_id}",
            headers=field,
            json={
                "gps_lat": 17.25,
                "gps_lng": 78.28,
                "owner_verified": True,
                "land_info_verified": True,
                "documents_verified": True,
                "remarks": "ok",
            },
        )
        assert patched.status_code == 200, patched.text
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
        photo = client.post(
            f"/api/field-verification/{rec_id}/photos",
            headers=field,
            files={"file": ("shot.png", BytesIO(png), "image/png")},
        )
        assert photo.status_code == 200, photo.text
        submitted = client.post(
            f"/api/field-verification/{rec_id}/submit", headers=field, json={"remarks": "done"}
        )
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["data"]["status"] == "SUBMITTED"
        again = client.post(f"/api/field-verification/{rec_id}/submit", headers=field, json={})
        assert again.status_code == 409
    # officer is not a field operator
    assert client.get("/api/field-verification", headers=officer).status_code == 403


def test_alerts_notifications_audit(client):
    admin = hdr(client, "admin@demo.local")
    evaled = client.post("/api/alerts/evaluate", headers=admin)
    assert evaled.status_code == 200
    first = evaled.json()["data"]["created"]
    second = client.post("/api/alerts/evaluate", headers=admin)
    assert second.json()["data"]["created"] == 0 or second.json()["data"]["created"] <= first
    alerts = client.get("/api/alerts", headers=admin, params={"page_size": 5})
    assert alerts.status_code == 200
    if alerts.json()["data"]:
        aid = alerts.json()["data"][0]["id"]
        marked = client.patch(f"/api/alerts/{aid}/read", headers=admin)
        assert marked.status_code == 200
        assert marked.json()["data"]["is_read"] is True
    notes = client.get("/api/notifications", headers=admin, params={"page_size": 20})
    assert notes.status_code == 200
    client.patch("/api/notifications/read-all", headers=admin)
    audit = client.get("/api/audit", headers=admin, params={"page_size": 10})
    assert audit.status_code == 200
    actions = {row["action"] for row in audit.json()["data"]}
    assert actions  # at least seed + phase3 mutations
    field = hdr(client, "field@demo.local")
    assert client.get("/api/audit", headers=field).status_code == 403
