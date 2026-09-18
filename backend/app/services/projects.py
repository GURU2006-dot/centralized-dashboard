from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.audit import AuditLog
from app.models.project import Project
from app.models.user import User
from app.repositories.projects import ProjectRepository
from app.schemas.common import as_float
from app.schemas.projects import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def list_projects(self, user: User, **kwargs) -> tuple[list[dict], int]:
        rows, total = self.repo.list_filtered(user, **kwargs)
        data = [
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "purpose": p.purpose,
                "state_code": p.state_code,
                "district_code": p.district_code,
                "area_ha": as_float(p.estimated_area_ha),
                "status": p.status,
                "current_stage": p.current_stage,
                "data_source": p.data_source,
            }
            for p in rows
        ]
        return data, total

    def get(self, user: User, project_id: UUID) -> dict:
        project = self.repo.get_scoped(user, project_id)
        if project is None:
            raise AppError(404, "NOT_FOUND", "Project not found")
        extra = self.repo.summaries(project.id)
        return {
            "id": project.id,
            "code": project.code,
            "name": project.name,
            "purpose": project.purpose,
            "requiring_body": project.requiring_body,
            "state_code": project.state_code,
            "district_code": project.district_code,
            "estimated_area_ha": as_float(project.estimated_area_ha),
            "estimated_compensation_inr": as_float(project.estimated_compensation_inr),
            "start_date": project.start_date,
            "expected_end_date": project.expected_end_date,
            "status": project.status,
            "current_stage": project.current_stage,
            "data_source": project.data_source,
            **extra,
        }

    def create(self, user: User, body: ProjectCreate) -> dict:
        if self.repo.get_by_code(body.code):
            raise AppError(409, "CONFLICT", "Project code already exists")
        project = Project(
            id=uuid4(),
            code=body.code,
            name=body.name,
            purpose=body.purpose,
            requiring_body=body.requiring_body,
            state_code=body.state_code,
            district_code=body.district_code,
            estimated_area_ha=body.estimated_area_ha,
            estimated_compensation_inr=body.estimated_compensation_inr,
            start_date=body.start_date,
            expected_end_date=body.expected_end_date,
            status=body.status,
            current_stage=body.current_stage,
            created_by=user.id,
            data_source="SYNTHETIC",
        )
        self.repo.add(project)
        self.db.add(
            AuditLog(
                user_id=user.id,
                action="PROJECT_CREATED",
                entity_type="project",
                entity_id=str(project.id),
                extra_metadata={"code": project.code},
            )
        )
        self.db.commit()
        return self.get(user, project.id)

    def update(self, user: User, project_id: UUID, body: ProjectUpdate) -> dict:
        project = self.repo.get_scoped(user, project_id)
        if project is None:
            raise AppError(404, "NOT_FOUND", "Project not found")
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(project, key, value)
        self.db.add(
            AuditLog(
                user_id=user.id,
                action="PROJECT_UPDATED",
                entity_type="project",
                entity_id=str(project.id),
                extra_metadata={"fields": list(data.keys())},
            )
        )
        self.db.commit()
        return self.get(user, project.id)
