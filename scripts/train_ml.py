#!/usr/bin/env python3
"""Train the synthetic delay-risk forest. Not invoked from HTTP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.train import train  # noqa: E402

if __name__ == "__main__":
    metrics = train()
    print(json.dumps({k: metrics[k] for k in ("accuracy", "f1_macro", "roc_auc_ovr", "n_train", "n_test", "model_version")}, indent=2))
