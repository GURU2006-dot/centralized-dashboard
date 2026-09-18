from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.parcel import LandParcel
from app.models.user import User
from app.repositories.parcels import ParcelRepository
from app.schemas.common import SYNTHETIC_DISCLAIMER, as_float


class ParcelService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ParcelRepository(db)

    def list_parcels(self, user: User, **kwargs) -> tuple[list[dict], int]:
        rows, total = self.repo.list_filtered(user, **kwargs)
        counts = self.repo.owner_counts([p.id for p in rows])
        data = []
        for p in rows:
            data.append(
                {
                    "id": p.id,
                    "ulpin": p.ulpin,
                    "khasra_number": p.khasra_number,
                    "village": p.village,
                    "tehsil": p.tehsil,
                    "state_code": p.state_code,
                    "district_code": p.district_code,
                    "area_ha": as_float(p.area_ha),
                    "project_id": p.project_id,
                    "project_code": p.project.code if p.project else None,
                    "acquisition_status": p.acquisition_status,
                    "current_stage": p.current_stage,
                    "data_source": p.data_source,
                    "owner_count": counts.get(p.id, 0),
                }
            )
        return data, total

    def get(self, user: User, parcel_id: UUID) -> dict:
        parcel = self.repo.get_scoped(user, parcel_id)
        if parcel is None:
            raise AppError(404, "NOT_FOUND", "Parcel not found")
        owners = [
            {
                "name": link.owner.name if link.owner else "Unknown",
                "ownership_type": link.ownership_type,
                "share_pct": as_float(link.ownership_share_pct),
            }
            for link in parcel.ownerships
        ]
        project = None
        if parcel.project:
            project = {
                "id": parcel.project.id,
                "code": parcel.project.code,
                "name": parcel.project.name,
            }
        return {
            "id": parcel.id,
            "ulpin": parcel.ulpin,
            "khasra_number": parcel.khasra_number,
            "village": parcel.village,
            "tehsil": parcel.tehsil,
            "state_code": parcel.state_code,
            "district_code": parcel.district_code,
            "area_ha": as_float(parcel.area_ha),
            "project": project,
            "acquisition_status": parcel.acquisition_status,
            "current_stage": parcel.current_stage,
            "owners": owners,
            "location": self._centroid(parcel),
            "geometry": self._geojson_feature(parcel),
            "data_source": parcel.data_source,
        }

    def _centroid(self, parcel: LandParcel) -> dict[str, float] | None:
        if parcel.centroid is None:
            return None
        row = self.db.execute(
            text(
                "SELECT ST_Y(centroid::geometry) AS lat, ST_X(centroid::geometry) AS lng "
                "FROM land_parcels WHERE id = :id"
            ),
            {"id": parcel.id},
        ).first()
        if not row or row[0] is None:
            return None
        return {"lat": float(row[0]), "lng": float(row[1])}

    def _geojson_feature(self, parcel: LandParcel) -> dict:
        geometry = parcel.geometry_geojson
        if geometry is None and parcel.geom is not None:
            raw = self.db.scalar(
                select(func.ST_AsGeoJSON(LandParcel.geom)).where(LandParcel.id == parcel.id)
            )
            if raw:
                import json

                geometry = json.loads(raw)
        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "ulpin": parcel.ulpin,
                "khasra_number": parcel.khasra_number,
                "data_source": parcel.data_source,
                "disclaimer": SYNTHETIC_DISCLAIMER,
            },
        }
