#!/usr/bin/env python3
"""Drop and recreate the demo schema, then reseed SYNTHETIC data."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.db import engine  # noqa: E402


def reset_schema() -> None:
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO nlamp"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        conn.commit()


def alembic_upgrade() -> None:
    subprocess.check_call(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(ROOT / "backend"),
    )


def seed() -> None:
    from seed_db import run

    run()


EXPECTED = {
    "projects": 8,
    "land_parcels": 80,
    "acquisition_cases": 60,
    "proposals": 8,
    "compensation": 32,
    "affected_families": 51,
    "rehabilitation": 17,
    "resettlement": 17,
    "possession": 16,
    "field_verifications": 8,
    "alerts": 12,
    "notifications": 8,
    "ml_predictions": 24,
    "users": 4,
}


if __name__ == "__main__":
    print("Resetting schema…")
    reset_schema()
    print("Running Alembic migrations…")
    alembic_upgrade()
    print("Seeding SYNTHETIC data…")
    seed()
    print("Demo database restored.")
    print("Expected baseline (SYNTHETIC):")
    for key, value in EXPECTED.items():
        print(f"  {key}: {value}")
