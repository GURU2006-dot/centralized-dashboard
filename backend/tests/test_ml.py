from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.dataset import generate_synthetic
from app.ml.features import FEATURE_NAMES, category_from_score_100, score_100, vector_from_dict
from app.ml.predictor import predict_features
from app.ml.train import train


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/api/auth/login", json={"email": email, "password": "Demo@1234"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}


def test_feature_vector_order_and_missing():
    empty = vector_from_dict({})
    assert len(empty) == len(FEATURE_NAMES)
    assert empty == [0.0] * len(FEATURE_NAMES)
    named = vector_from_dict({"days_in_current_stage": 42, "unknown": 9})
    assert named[FEATURE_NAMES.index("days_in_current_stage")] == 42
    assert named[0] == 0.0


def test_score_thresholds():
    assert category_from_score_100(0) == "LOW"
    assert category_from_score_100(39) == "LOW"
    assert category_from_score_100(40) == "MEDIUM"
    assert category_from_score_100(70) == "HIGH"
    assert 0 <= score_100(0.874) <= 100


def test_synthetic_dataset_reproducible():
    a, la = generate_synthetic(n=50, seed=42)
    b, lb = generate_synthetic(n=50, seed=42)
    assert np.allclose(a, b)
    assert np.array_equal(la, lb)
    assert a.shape[1] == len(FEATURE_NAMES)


def test_training_and_prediction_range(tmp_path):
    metrics = train(tmp_path)
    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["f1_macro"] <= 1
    from app.ml.predictor import load_model

    bundle = load_model(tmp_path / "delay_risk_model.joblib")
    features = {name: 0 for name in FEATURE_NAMES}
    features["days_in_current_stage"] = 80
    features["compensation_paid_ratio"] = 0.1
    features["project_is_delayed"] = 1
    out = predict_features(features, bundle)
    assert 0 <= out["risk_score"] <= 100
    assert out["risk_category"] in ("LOW", "MEDIUM", "HIGH")
    assert out["trained_on"] == "SYNTHETIC"


def test_predict_api_auth_and_persist(client):
    assert client.post("/api/ml/predict/00000000-0000-4000-8000-000000000099").status_code == 401
    field = auth(client, "field@demo.local")
    listing = client.get("/api/acquisitions", headers=auth(client, "admin@demo.local"), params={"page_size": 1})
    cid = listing.json()["data"][0]["id"]
    assert client.post(f"/api/ml/predict/{cid}", headers=field).status_code == 403
    admin = auth(client, "admin@demo.local")
    missing = client.post(
        "/api/ml/predict/00000000-0000-4000-8000-000000000099", headers=admin
    )
    assert missing.status_code == 404
    first = client.post(f"/api/ml/predict/{cid}", headers=admin)
    assert first.status_code == 200, first.text
    body = first.json()["data"]
    assert 0 <= body["risk_score"] <= 100
    assert body["risk_category"] in ("LOW", "MEDIUM", "HIGH")
    assert body["trained_on"] == "SYNTHETIC"
    hist = client.get(f"/api/ml/predictions/{cid}", headers=admin)
    assert hist.status_code == 200
    assert len(hist.json()["data"]) >= 1
    second = client.post(f"/api/ml/predict/{cid}", headers=admin)
    assert second.status_code == 200
    if body["risk_category"] == "HIGH":
        assert second.json()["data"]["alerts_created"] == 0
    metrics = client.get("/api/ml/metrics", headers=admin)
    assert metrics.status_code == 200
    assert metrics.json()["data"]["trained_on"] == "SYNTHETIC"


def test_gis_bulk_geojson(client):
    admin = auth(client, "admin@demo.local")
    r = client.get("/api/gis/parcels", headers=admin, params={"limit": 10})
    assert r.status_code == 200
    fc = r.json()["data"]
    assert fc["type"] == "FeatureCollection"
    assert "features" in fc
    if fc["features"]:
        props = fc["features"][0]["properties"]
        assert "ulpin" in props
        assert "khasra_number" in props
        assert "tehsil" in props
        assert "district_code" in props
        assert "state_code" in props


def test_gis_empty_filter_results(client):
    admin = auth(client, "admin@demo.local")
    r = client.get("/api/gis/parcels", headers=admin, params={"state": "ZZ_NONEXISTENT"})
    assert r.status_code == 200
    fc = r.json()["data"]
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 0

