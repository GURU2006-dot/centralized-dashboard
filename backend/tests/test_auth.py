from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import JWT_ALGORITHM, JWT_ISSUER, JWT_SECRET_KEY
from app.db import SessionLocal
from app.main import app
from app.models.user import User


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def login(client: TestClient, email: str, password: str = "Demo@1234"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_docs_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


@pytest.mark.parametrize(
    "email",
    [
        "admin@demo.local",
        "officer@demo.local",
        "approver@demo.local",
        "field@demo.local",
    ],
)
def test_valid_login(client, email):
    r = login(client, email)
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert "hashed_password" not in body["user"]
    assert "password" not in body["user"]
    assert body["user"]["email"] == email


def test_invalid_password(client):
    r = login(client, "admin@demo.local", "wrong")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_unknown_user(client):
    r = login(client, "nobody@demo.local", "Demo@1234")
    assert r.status_code == 401


def test_me_and_missing_token(client):
    assert client.get("/api/auth/me").status_code == 401
    token = login(client, "admin@demo.local").json()["data"]["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["data"]["role"] == "ADMIN"


def test_invalid_token(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_expired_token(client):
    token = jwt.encode(
        {
            "sub": "00000000-0000-4000-8000-000000000001",
            "role": "ADMIN",
            "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp()),
            "iss": JWT_ISSUER,
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_inactive_user(client):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "field@demo.local").one()
        user.is_active = False
        db.commit()
        r = login(client, "field@demo.local")
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "ACCOUNT_DISABLED"
    finally:
        user = db.query(User).filter(User.email == "field@demo.local").one()
        user.is_active = True
        db.commit()
        db.close()
