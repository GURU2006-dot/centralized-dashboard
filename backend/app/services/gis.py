from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.acquisition import AcquisitionCase
from app.models.ml_prediction import MLPrediction
from app.models.parcel import LandParcel
from app.models.project import Project
from app.models.user import User
from app.schemas.common import SYNTHETIC_DISCLAIMER
from app.services.scope import apply_parcel_scope


class GISService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def parcel_features(
        self,
        user: User,
        *,
        state: str | None,
        district: str | None,
        project_id: UUID | None,
        status: str | None,
        stage: str | None,
        risk_level: str | None,
        limit: int = 80,
    ) -> dict:
        risk = (
            select(
                MLPrediction.acquisition_case_id,
                MLPrediction.risk_level,
                MLPrediction.risk_score,
            )
            .distinct(MLPrediction.acquisition_case_id)
            .order_by(MLPrediction.acquisition_case_id, MLPrediction.predicted_at.desc())
            .subquery()
        )
        stmt = (
            select(
                LandParcel,
                AcquisitionCase.id,
                AcquisitionCase.case_number,
                AcquisitionCase.current_stage,
                Project.code,
                risk.c.risk_level,
                risk.c.risk_score,
                func.ST_AsGeoJSON(LandParcel.geom),
            )
            .outerjoin(AcquisitionCase, AcquisitionCase.parcel_id == LandParcel.id)
            .outerjoin(Project, LandParcel.project_id == Project.id)
            .outerjoin(risk, risk.c.acquisition_case_id == AcquisitionCase.id)
        )
        stmt = apply_parcel_scope(stmt, self.db, user)
        if state:
            stmt = stmt.where(LandParcel.state_code == state)
        if district:
            stmt = stmt.where(LandParcel.district_code == district)
        if project_id:
            stmt = stmt.where(LandParcel.project_id == project_id)
        if status:
            stmt = stmt.where(LandParcel.acquisition_status == status)
        if stage:
            stmt = stmt.where(AcquisitionCase.current_stage == stage)
        if risk_level:
            stmt = stmt.where(risk.c.risk_level == risk_level)
        stmt = stmt.where(LandParcel.geom.is_not(None)).limit(min(max(limit, 1), 120))
        features = []
        for parcel, case_id, case_number, current_stage, project_code, level, score, geo in self.db.execute(stmt):
            geometry = None
            if geo:
                geometry = json.loads(geo)
            elif parcel.geometry_geojson:
                geometry = parcel.geometry_geojson
            if not geometry:
                continue
            raw = float(score) if score is not None else None
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": str(parcel.id),
                        "ulpin": parcel.ulpin,
                        "khasra_number": parcel.khasra_number,
                        "village": parcel.village,
                        "tehsil": parcel.tehsil,
                        "district_code": parcel.district_code,
                        "state_code": parcel.state_code,
                        "area_ha": float(parcel.area_ha) if parcel.area_ha is not None else None,
                        "acquisition_status": parcel.acquisition_status,
                        "current_stage": current_stage or parcel.current_stage,
                        "project": project_code,
                        "case_id": str(case_id) if case_id else None,
                        "case_number": case_number,
                        "risk_level": level,
                        "risk_score": round(raw * 100, 1) if raw is not None else None,
                        "data_source": parcel.data_source,
                        "disclaimer": SYNTHETIC_DISCLAIMER,
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}
