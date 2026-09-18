from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import DATABASE_URL  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(DATABASE_URL, future=True)
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine) -> Session:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
