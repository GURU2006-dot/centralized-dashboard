from __future__ import annotations

from fastapi import APIRouter

from app.api import (
    acquisitions,
    alerts,
    audit,
    auth,
    compensation,
    dashboard,
    documents,
    families,
    field_verification,
    gis,
    integrations,
    ml,
    notifications,
    parcels,
    possession,
    projects,
    proposals,
    rehabilitation,
    resettlement,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(projects.router)
api_router.include_router(parcels.router)
api_router.include_router(proposals.router)
api_router.include_router(acquisitions.router)
api_router.include_router(compensation.router)
api_router.include_router(possession.router)
api_router.include_router(rehabilitation.router)
api_router.include_router(resettlement.router)
api_router.include_router(families.router)
api_router.include_router(field_verification.router)
api_router.include_router(documents.router)
api_router.include_router(alerts.router)
api_router.include_router(notifications.router)
api_router.include_router(audit.router)
api_router.include_router(ml.router)
api_router.include_router(gis.router)
api_router.include_router(integrations.router)
