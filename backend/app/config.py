"""Environment configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _split_origins(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://nlamp:nlamp@localhost:5432/nlamp",
)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "nlamp-dev-only-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
APP_ENV = os.getenv("APP_ENV", "development")
CORS_ORIGINS = _split_origins(
    os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
)
JWT_ISSUER = "nlamp-prototype"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(ROOT / "data" / "uploads")))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
INTEGRATION_MODE = os.getenv("INTEGRATION_MODE", "mock").strip().lower()
