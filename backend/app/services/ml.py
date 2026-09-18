from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.ml.features import MODEL_NAME, MODEL_VERSION
from app.ml.predictor import ModelNotLoaded, predict_features
from app.ml.train import METRICS_PATH
from app.models.acquisition import AcquisitionCase
from app.models.ml_prediction import MLPrediction
from app.models.user import User
from app.repositories.acquisitions import AcquisitionRepository
from app.services.alerts import AlertService
from app.services.audit import AuditService
from app.services.ml_features import assemble_features
from app.services.scope import apply_project_scope


class MLService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cases = AcquisitionRepository(db)
        self.alerts = AlertService(db)
        self.audit = AuditService(db)

    def _predict_payload(self, features: dict) -> dict:
        try:
            return predict_features(features)
        except ModelNotLoaded as exc:
            raise AppError(503, "MODEL_NOT_LOADED", "Delay-risk model is not trained") from exc

    def predict_case(self, user: User, case_id: UUID, *, commit: bool = True) -> dict:
        case = self.cases.get_scoped(user, case_id)
        if case is None:
            raise AppError(404, "NOT_FOUND", "Acquisition case not found")
        features = assemble_features(self.db, case)
        result = self._predict_payload(features)
        row = MLPrediction(
            id=uuid4(),
            acquisition_case_id=case.id,
            project_id=case.project_id,
            risk_level=result["risk_category"],
            risk_score=result["risk_score_raw"],
            features={
                "values": result["features"],
                "indicators": result["indicators"],
                "class_probabilities": result["class_probabilities"],
            },
            model_version=result["model_version"],
            trained_on="SYNTHETIC",
            predicted_at=datetime.now(timezone.utc),
            predicted_by=user.id,
        )
        self.db.add(row)
        alerts_created = 0
        if result["risk_category"] == "HIGH":
            alerts_created = self.alerts.emit_ml_high(
                case,
                score_100=result["risk_score"],
            )
        self.audit.record(
            user,
            "ML_PREDICTED",
            "acquisition_case",
            case.id,
            {"risk_category": result["risk_category"], "risk_score": result["risk_score"]},
        )
        if commit:
            self.db.commit()
        return self._serialize(row, case, result, alerts_created)

    def predict_batch(self, user: User, *, project_id: UUID | None, limit: int = 60) -> dict:
        stmt = apply_project_scope(select(AcquisitionCase), self.db, user)
        if project_id:
            stmt = stmt.where(AcquisitionCase.project_id == project_id)
        stmt = stmt.order_by(AcquisitionCase.case_number).limit(min(max(limit, 1), 80))
        cases = list(self.db.scalars(stmt).unique().all())
        items = []
        for case in cases:
            items.append(self.predict_case(user, case.id, commit=False))
        self.db.commit()
        return {"predicted": len(items), "results": items}

    def history(self, user: User, case_id: UUID) -> list[dict]:
        case = self.cases.get_scoped(user, case_id)
        if case is None:
            raise AppError(404, "NOT_FOUND", "Acquisition case not found")
        rows = list(
            self.db.scalars(
                select(MLPrediction)
                .where(MLPrediction.acquisition_case_id == case_id)
                .order_by(MLPrediction.predicted_at.desc())
            ).all()
        )
        return [self._serialize(r, case, None, 0) for r in rows]

    def latest(self, user: User, case_id: UUID) -> dict | None:
        hist = self.history(user, case_id)
        return hist[0] if hist else None

    def summary(self, user: User, *, project_id: UUID | None = None) -> dict:
        latest = (
            select(
                MLPrediction.acquisition_case_id,
                MLPrediction.risk_level,
                MLPrediction.risk_score,
                MLPrediction.project_id,
            )
            .distinct(MLPrediction.acquisition_case_id)
            .order_by(MLPrediction.acquisition_case_id, MLPrediction.predicted_at.desc())
            .subquery()
        )
        stmt = select(latest)
        if project_id:
            stmt = stmt.where(latest.c.project_id == project_id)
        rows = self.db.execute(stmt).all()
        high = sum(1 for r in rows if r.risk_level == "HIGH")
        med = sum(1 for r in rows if r.risk_level == "MEDIUM")
        low = sum(1 for r in rows if r.risk_level == "LOW")
        avg = (sum(float(r.risk_score or 0) for r in rows) / len(rows)) if rows else 0.0
        return {
            "cases_scored": len(rows),
            "high_risk_cases": high,
            "medium_risk_cases": med,
            "low_risk_cases": low,
            "average_risk_score": round(avg * 100, 1),
            "average_risk_score_raw": round(avg, 4),
            "aggregation": "Latest prediction per case. Display score is stored 0–1 × 100.",
            "disclaimer": "Prototype scores on synthetic data. Not a statutory decision.",
        }

    def analytics(self, user: User) -> dict:
        latest = (
            select(
                MLPrediction.acquisition_case_id,
                MLPrediction.risk_level,
                MLPrediction.risk_score,
                MLPrediction.project_id,
            )
            .distinct(MLPrediction.acquisition_case_id)
            .order_by(MLPrediction.acquisition_case_id, MLPrediction.predicted_at.desc())
            .subquery()
        )
        from app.models.project import Project

        stage_rows = self.db.execute(
            select(AcquisitionCase.current_stage, latest.c.risk_level, func.count())
            .join(latest, latest.c.acquisition_case_id == AcquisitionCase.id)
            .group_by(AcquisitionCase.current_stage, latest.c.risk_level)
        ).all()
        state_rows = self.db.execute(
            select(Project.state_code, latest.c.risk_level, func.count())
            .join(Project, Project.id == latest.c.project_id)
            .group_by(Project.state_code, latest.c.risk_level)
        ).all()
        by_stage: dict[str, dict[str, int]] = {}
        for stage, level, n in stage_rows:
            by_stage.setdefault(stage, {"LOW": 0, "MEDIUM": 0, "HIGH": 0})
            by_stage[stage][level] = int(n)
        by_state: dict[str, dict[str, int]] = {}
        for state, level, n in state_rows:
            by_state.setdefault(state, {"LOW": 0, "MEDIUM": 0, "HIGH": 0})
            by_state[state][level] = int(n)
        return {
            "by_stage": [{"stage": k, **v} for k, v in sorted(by_stage.items())],
            "by_state": [{"state_code": k, **v} for k, v in sorted(by_state.items())],
            "summary": self.summary(user),
        }

    def metrics(self) -> dict:
        if not METRICS_PATH.exists():
            raise AppError(503, "MODEL_NOT_LOADED", "Metrics file is missing — train the model")
        data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        data["thresholds"] = {
            "LOW": "0–39",
            "MEDIUM": "40–69",
            "HIGH": "70–100",
            "note": "Prototype conventions on display score (P(HIGH)×100). Not government standards.",
        }
        return data

    @staticmethod
    def _serialize(row: MLPrediction, case: AcquisitionCase, result: dict | None, alerts_created: int) -> dict:
        raw = float(row.risk_score or 0)
        display = round(raw * 100.0, 1)
        snapshot = row.features or {}
        return {
            "id": row.id,
            "case_id": row.acquisition_case_id,
            "case_number": case.case_number if case else None,
            "project_id": row.project_id,
            "risk_score": display,
            "risk_score_raw": round(raw, 4),
            "risk_category": row.risk_level,
            "model": MODEL_NAME,
            "model_version": row.model_version,
            "trained_on": row.trained_on,
            "predicted_at": row.predicted_at,
            "indicators": (result["indicators"] if result else snapshot.get("indicators") or []),
            "features": (result["features"] if result else snapshot.get("values") or {}),
            "alerts_created": alerts_created,
            "disclaimer": (
                "This model is a prototype trained on synthetic demonstration data "
                "and is not a validated government decision-making model. "
                "Scores are decision-support indicators, not statutory decisions."
            ),
        }
