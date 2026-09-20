from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest
from fastapi.testclient import TestClient

from app.main import app

SENSITIVE = ("id_number", "phone", "address", "hashed_password", "password")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth_header(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/api/auth/login", json={"email": email, "password": "Demo@1234"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}


def test_unauthenticated_is_401(client):
    for path in (
        "/api/dashboard/kpis",
        "/api/projects",
        "/api/parcels",
        "/api/acquisitions",
    ):
        assert client.get(path).status_code == 401


def test_field_officer_cannot_create_project(client):
    headers = auth_header(client, "field@demo.local")
    r = client.post(
        "/api/projects",
        headers=headers,
        json={
            "code": "NOPE-1",
            "name": "Should fail",
            "purpose": "RBAC test",
            "state_code": "TG",
        },
    )
    assert r.status_code == 403


def test_dashboard_kpis_from_db(client):
    headers = auth_header(client, "admin@demo.local")
    r = client.get("/api/dashboard/kpis", headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_projects"] == 8
    assert data["area_notified_ha"] >= 0
    assert data["area_acquired_ha"] >= 0
    assert data["area_notified_ha"] != data["area_acquired_ha"] or data["area_notified_ha"] == 0
    assert data["affected_families"] > 0
    assert "rr_progress" in data


def test_dashboard_charts_and_filters(client):
    headers = auth_header(client, "admin@demo.local")
    charts = client.get("/api/dashboard/charts", headers=headers)
    assert charts.status_code == 200
    body = charts.json()["data"]
    assert "stage_distribution" in body
    assert "state_wise_progress" in body
    assert "compensation" in body
    assert "rr_status" in body
    assert "risk" in body
    filters = client.get("/api/dashboard/filters", headers=headers)
    assert filters.status_code == 200
    assert len(filters.json()["data"]["states"]) == 3


def test_dashboard_state_filter(client):
    headers = auth_header(client, "admin@demo.local")
    all_k = client.get("/api/dashboard/kpis", headers=headers).json()["data"]
    tg = client.get("/api/dashboard/kpis", headers=headers, params={"state": "TG"}).json()["data"]
    assert tg["total_projects"] < all_k["total_projects"]
    assert tg["total_projects"] == 3


def test_officer_is_state_scoped(client):
    admin = auth_header(client, "admin@demo.local")
    officer = auth_header(client, "officer@demo.local")
    admin_n = client.get("/api/projects", headers=admin, params={"page_size": 100}).json()["meta"]["total"]
    officer_n = client.get("/api/projects", headers=officer, params={"page_size": 100}).json()["meta"]["total"]
    assert admin_n == 8
    assert officer_n == 3
    for row in client.get("/api/projects", headers=officer, params={"page_size": 100}).json()["data"]:
        assert row["state_code"] == "TG"


def test_projects_list_pagination_search(client):
    headers = auth_header(client, "admin@demo.local")
    page1 = client.get("/api/projects", headers=headers, params={"page": 1, "page_size": 3})
    assert page1.status_code == 200
    assert len(page1.json()["data"]) == 3
    assert page1.json()["meta"]["total"] == 8
    search = client.get("/api/projects", headers=headers, params={"search": "Metro"})
    assert search.status_code == 200
    assert search.json()["meta"]["total"] >= 1
    delayed = client.get("/api/projects", headers=headers, params={"status": "DELAYED"})
    assert delayed.json()["meta"]["total"] >= 1


def test_project_detail_and_404(client):
    headers = auth_header(client, "admin@demo.local")
    listing = client.get("/api/projects", headers=headers).json()["data"]
    pid = listing[0]["id"]
    detail = client.get(f"/api/projects/{pid}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["parcel_count"] >= 1
    assert "code" in body
    missing = client.get("/api/projects/00000000-0000-4000-8000-000000000099", headers=headers)
    assert missing.status_code == 404


def test_parcels_list_ulpin_and_sensitive_fields(client):
    headers = auth_header(client, "admin@demo.local")
    listing = client.get("/api/parcels", headers=headers, params={"page_size": 5})
    assert listing.status_code == 200
    assert listing.json()["meta"]["total"] >= 80
    row = listing.json()["data"][0]
    blob = str(listing.json())
    for key in SENSITIVE:
        assert key not in blob
    ulpin = row["ulpin"]
    found = client.get("/api/parcels", headers=headers, params={"ulpin": ulpin})
    assert found.json()["meta"]["total"] == 1
    detail = client.get(f"/api/parcels/{row['id']}", headers=headers)
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["geometry"]["type"] == "Feature"
    assert "owners" in data
    dumped = str(detail.json())
    for key in SENSITIVE:
        assert key not in dumped
    assert client.get(
        "/api/parcels/00000000-0000-4000-8000-000000000099", headers=headers
    ).status_code == 404


def test_field_officer_parcel_scope(client):
    headers = auth_header(client, "field@demo.local")
    r = client.get("/api/parcels", headers=headers, params={"page_size": 100})
    assert r.status_code == 200
    total = r.json()["meta"]["total"]
    assert 1 <= total <= 8


def test_acquisitions_list_detail_timeline(client):
    headers = auth_header(client, "admin@demo.local")
    listing = client.get("/api/acquisitions", headers=headers, params={"page_size": 10})
    assert listing.status_code == 200
    assert listing.json()["meta"]["total"] >= 60
    item = listing.json()["data"][0]
    cid = item["id"]
    detail = client.get(f"/api/acquisitions/{cid}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["case_number"]
    assert "notified_area_ha" in body
    timeline = client.get(f"/api/acquisitions/{cid}/timeline", headers=headers)
    assert timeline.status_code == 200
    events = timeline.json()["data"]["events"]
    assert len(events) >= 1
    assert "from_stage" in events[0]
    assert "to_stage" in events[0]
    assert client.get(
        "/api/acquisitions/00000000-0000-4000-8000-000000000099", headers=headers
    ).status_code == 404


def test_project_create_forbidden_for_approver(client):
    headers = auth_header(client, "approver@demo.local")
    r = client.post(
        "/api/projects",
        headers=headers,
        json={"code": "X-1", "name": "Nope", "purpose": "test", "state_code": "TG"},
    )
    assert r.status_code == 403
