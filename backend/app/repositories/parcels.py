from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.parcel import LandParcel, ParcelOwner
from app.models.project import Project
from app.models.user import User
from app.services.scope import apply_parcel_scope


class ParcelRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _base(self, user: User) -> Select:
        return apply_parcel_scope(select(LandParcel), self.db, user)

    def list_filtered(
        self,
        user: User,
        *,
        ulpin: str | None,
        khasra: str | None,
        village: str | None,
        tehsil: str | None,
        state: str | None,
        district: str | None,
        project_id: UUID | None,
        status: str | None,
        stage: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[LandParcel], int]:
        stmt = self._base(user).options(selectinload(LandParcel.project))
        if ulpin:
            stmt = stmt.where(LandParcel.ulpin.ilike(f"%{ulpin.strip()}%"))
        if khasra:
            stmt = stmt.where(LandParcel.khasra_number.ilike(f"%{khasra.strip()}%"))
        if village:
            stmt = stmt.where(LandParcel.village.ilike(f"%{village.strip()}%"))
        if tehsil:
            stmt = stmt.where(LandParcel.tehsil.ilike(f"%{tehsil.strip()}%"))
        if state:
            stmt = stmt.where(LandParcel.state_code == state)
        if district:
            stmt = stmt.where(LandParcel.district_code == district)
        if project_id:
            stmt = stmt.where(LandParcel.project_id == project_id)
        if status:
            stmt = stmt.where(LandParcel.acquisition_status == status)
        if stage:
            stmt = stmt.where(LandParcel.current_stage == stage)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(LandParcel.ulpin)
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return rows, int(total)

    def get_scoped(self, user: User, parcel_id: UUID) -> LandParcel | None:
        stmt = (
            self._base(user)
            .options(
                selectinload(LandParcel.project),
                selectinload(LandParcel.ownerships).selectinload(ParcelOwner.owner),
            )
            .where(LandParcel.id == parcel_id)
        )
        return self.db.scalars(stmt).first()

    def owner_counts(self, parcel_ids: list[UUID]) -> dict[UUID, int]:
        if not parcel_ids:
            return {}
        rows = self.db.execute(
            select(ParcelOwner.parcel_id, func.count())
            .where(ParcelOwner.parcel_id.in_(parcel_ids))
            .group_by(ParcelOwner.parcel_id)
        ).all()
        return {pid: int(n) for pid, n in rows}
