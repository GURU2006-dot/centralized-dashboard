"""FastAPI application entrypoint — Phase 2 backend foundation."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.config import APP_ENV, CORS_ORIGINS, DATABASE_URL
from app.db import engine
from app.errors import register_exception_handlers
from app.logging import get_logger, setup_logging

log = get_logger("nlamp")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    log.info("NLAMP API starting (env=%s)", APP_ENV)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("PostgreSQL connectivity check succeeded")
    except Exception:
        log.exception("PostgreSQL connectivity check failed")
        raise
    yield
    log.info("NLAMP API shutdown")


app = FastAPI(
    title="NLAMP API",
    description=(
        "National Land Acquisition Management Platform — SIH 26016 prototype. "
        "All operational data is SYNTHETIC demonstration data, not live government records."
    ),
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "NLAMP API",
        "docs": "/docs",
        "health": "/health",
        "data_source": "SYNTHETIC",
    }


# Silence unused import warning for DATABASE_URL documentation
_ = DATABASE_URL
