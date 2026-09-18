"""Load the trained forest and score a feature dict."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from app.ml.features import (
    FEATURE_NAMES,
    MODEL_NAME,
    MODEL_VERSION,
    category_from_score_100,
    risk_indicators,
    vector_from_dict,
)
from app.ml.train import MODEL_PATH

_CACHE: dict | None = None


class ModelNotLoaded(RuntimeError):
    pass


def load_model(path: Path | None = None) -> dict:
    global _CACHE
    target = path or MODEL_PATH
    if _CACHE is not None and path is None:
        return _CACHE
    if not target.exists():
        raise ModelNotLoaded(f"Model artifact missing at {target}")
    bundle = joblib.load(target)
    if path is None:
        _CACHE = bundle
    return bundle


def predict_features(features: dict, bundle: dict | None = None) -> dict:
    model_bundle = bundle or load_model()
    clf = model_bundle["model"]
    vec = np.asarray([vector_from_dict(features)], dtype=float)
    proba = clf.predict_proba(vec)[0]
    classes = list(model_bundle.get("classes") or clf.classes_)
    # sklearn classes_ may be ints 0,1,2 matching CLASSES order
    class_names = ["LOW", "MEDIUM", "HIGH"]
    mapping = {}
    for idx, p in enumerate(proba):
        label = classes[idx]
        if isinstance(label, (int, np.integer)):
            name = class_names[int(label)]
        else:
            name = str(label)
        mapping[name] = float(p)
    p_low = mapping.get("LOW", 0.0)
    p_med = mapping.get("MEDIUM", 0.0)
    p_high = mapping.get("HIGH", 0.0)
    # Risk index = expected class midpoint (0 / 50 / 100). Not P(delay), not calibrated.
    display = round(max(0.0, min(100.0, 0.0 * p_low + 50.0 * p_med + 100.0 * p_high)), 1)
    category = category_from_score_100(display)
    return {
        "risk_score": display,
        "risk_score_raw": round(display / 100.0, 4),
        "risk_category": category,
        "class_probabilities": {k: round(v, 4) for k, v in mapping.items()},
        "model": MODEL_NAME,
        "model_version": model_bundle.get("model_version") or MODEL_VERSION,
        "trained_on": model_bundle.get("trained_on") or "SYNTHETIC",
        "indicators": risk_indicators(features),
        "features": {name: features.get(name, 0) for name in FEATURE_NAMES},
    }
