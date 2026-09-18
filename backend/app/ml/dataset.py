"""Deterministic synthetic training rows. Not government historical records."""

from __future__ import annotations

import numpy as np

from app.ml.features import FEATURE_NAMES, LOW_MAX, MEDIUM_MAX, RANDOM_STATE, category_from_score_100


N_SAMPLES = 1200
CLASSES = ("LOW", "MEDIUM", "HIGH")


def generate_synthetic(n: int = N_SAMPLES, seed: int = RANDOM_STATE) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    rows = []
    labels = []
    for _ in range(n):
        stage_idx = int(rng.integers(1, 9))
        days_start = float(rng.integers(5, 400))
        days_stage = float(rng.integers(1, 90))
        events = float(rng.integers(1, 12))
        completed = max(0, stage_idx - 1)
        remaining = max(0, 8 - stage_idx)
        assessed = float(rng.uniform(0, 8_000_000))
        paid_ratio = float(rng.uniform(0, 1))
        unpaid = max(0.0, assessed * (1 - paid_ratio))
        field_done = float(rng.integers(0, 2))
        checks = float(rng.integers(0, 4)) if field_done else 0.0
        gps = float(rng.integers(0, 2)) if field_done else 0.0
        docs = float(rng.integers(0, 8))
        unverified = float(rng.integers(0, int(docs) + 1)) if docs else 0.0
        families = float(rng.integers(0, 12))
        displaced = float(rng.integers(0, int(families) + 1)) if families else 0.0
        project_area = float(rng.uniform(5, 400))
        parcel_area = float(rng.uniform(0.1, 8))
        delayed = float(rng.integers(0, 2))

        # Transparent heuristic + noise so labels are not independent of features.
        raw = 0.0
        raw += min(days_stage / 90.0, 1.0) * 22
        raw += (1.0 - paid_ratio) * 18
        raw += (1.0 - field_done) * 12
        raw += min(unverified / 5.0, 1.0) * 10
        raw += min(displaced / 8.0, 1.0) * 8
        raw += delayed * 12
        raw += min(days_start / 365.0, 1.0) * 10
        raw += (remaining / 8.0) * 8
        raw += float(rng.normal(0, 8))
        raw = float(np.clip(raw, 0, 100))
        label = category_from_score_100(raw)

        row = [
            stage_idx,
            days_start,
            days_stage,
            events,
            completed,
            remaining,
            assessed,
            paid_ratio,
            unpaid,
            field_done,
            checks,
            gps,
            docs,
            unverified,
            families,
            displaced,
            project_area,
            parcel_area,
            delayed,
        ]
        assert len(row) == len(FEATURE_NAMES)
        rows.append(row)
        labels.append(CLASSES.index(label))
    return np.asarray(rows, dtype=float), np.asarray(labels, dtype=int)


# Silence unused import warning for documentation of thresholds.
_ = (LOW_MAX, MEDIUM_MAX)
