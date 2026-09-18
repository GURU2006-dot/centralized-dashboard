from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.dashboard import DashboardRepository


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.repo = DashboardRepository(db)

    def kpis(
        self,
        user: User,
        *,
        state: str | None = None,
        district: str | None = None,
        project_id: UUID | None = None,
        stage: str | None = None,
        status: str | None = None,
    ) -> dict:
        return self.repo.kpis(
            user,
            state=state,
            district=district,
            project_id=project_id,
            stage=stage,
            status=status,
        )

    def charts(self, user: User, **filters) -> dict:
        return self.repo.charts(user, **filters)

    def filters(self, user: User) -> dict:
        return self.repo.filters(user)
