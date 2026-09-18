"""Train RandomForestClassifier on synthetic data. Never called from a request."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from app.ml.dataset import CLASSES, generate_synthetic
from app.ml.features import FEATURE_NAMES, MODEL_NAME, MODEL_VERSION, RANDOM_STATE

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "delay_risk_model.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"


def train(output_dir: Path | None = None) -> dict:
    out = output_dir or ARTIFACT_DIR
    out.mkdir(parents=True, exist_ok=True)
    X, y = generate_synthetic()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    clf = RandomForestClassifier(
        n_estimators=80,
        max_depth=8,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)
    proba = clf.predict_proba(X_test)
    metrics = {
        "model": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "trained_on": "SYNTHETIC",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": int(len(X)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "feature_names": list(FEATURE_NAMES),
        "classes": list(CLASSES),
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision_macro": round(float(precision_score(y_test, pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_test, pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_test, pred, average="macro", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "feature_importances": {
            name: round(float(v), 4) for name, v in zip(FEATURE_NAMES, clf.feature_importances_)
        },
        "disclaimer": (
            "This model is a prototype trained on synthetic demonstration data "
            "and is not a validated government decision-making model."
        ),
    }
    try:
        metrics["roc_auc_ovr"] = round(
            float(roc_auc_score(y_test, proba, multi_class="ovr", average="macro")), 4
        )
    except ValueError:
        metrics["roc_auc_ovr"] = None
    bundle = {
        "model": clf,
        "feature_names": list(FEATURE_NAMES),
        "classes": list(CLASSES),
        "model_version": MODEL_VERSION,
        "trained_on": "SYNTHETIC",
    }
    joblib.dump(bundle, out / MODEL_PATH.name)
    (out / METRICS_PATH.name).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    result = train()
    print(json.dumps({k: result[k] for k in ("accuracy", "f1_macro", "n_train", "n_test")}, indent=2))
