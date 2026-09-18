from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/api/auth/login", json={"email": email, "password": "Demo@1234"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}


def test_status_is_mock(client):
    assert client.get("/api/integrations/status").status_code == 401
    admin = auth(client, "admin@demo.local")
    r = client.get("/api/integrations/status", headers=admin)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["mode"] == "mock"
    names = {s["name"] for s in data["systems"]}
    assert {"land_records", "cadastral_maps", "registration", "financial"} <= names
    for s in data["systems"]:
        assert s["implementation"] == "MOCK"
        assert s["mode"] == "MOCK"


def test_lookup_and_unknown(client):
    admin = auth(client, "admin@demo.local")
    parcel = client.get("/api/parcels", headers=admin, params={"page_size": 1}).json()["data"][0]
    ulpin = parcel["ulpin"]
    ok = client.post(
        "/api/integrations/land-records/lookup",
        headers=admin,
        json={"ulpin": ulpin},
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()["data"]
    assert body["mode"] == "MOCK"
    assert body["data_source"] == "MOCK_ADAPTER"
    assert "id_number" not in str(body)
    missing = client.post(
        "/api/integrations/land-records/lookup",
        headers=admin,
        json={"ulpin": "ZZZNOPE0000000"},
    )
    assert missing.status_code == 404
    field = auth(client, "field@demo.local")
    assert (
        client.post(
            "/api/integrations/land-records/lookup",
            headers=field,
            json={"ulpin": ulpin},
        ).status_code
        == 403
    )


def test_mock_sync_admin_only(client):
    officer = auth(client, "officer@demo.local")
    assert client.post("/api/integrations/financial/sync", headers=officer).status_code == 403
    admin = auth(client, "admin@demo.local")
    r = client.post("/api/integrations/financial/sync", headers=admin)
    assert r.status_code == 200
    assert r.json()["data"]["mode"] == "MOCK"
    assert r.json()["data"]["synced"] == 0
