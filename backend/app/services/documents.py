from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.errors import AppError
from app.models.document import Document
from app.models.user import User
from app.services.audit import AuditService

ALLOWED_MIME = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _serialize(row: Document) -> dict:
    return {
        "id": row.id,
        "public_id": row.public_id,
        "name": row.name,
        "doc_type": row.doc_type,
        "project_id": row.project_id,
        "parcel_id": row.parcel_id,
        "proposal_id": row.proposal_id,
        "acquisition_case_id": row.acquisition_case_id,
        "mime_type": row.mime_type,
        "byte_size": row.byte_size,
        "uploaded_by": row.uploaded_by,
        "uploaded_at": row.uploaded_at,
        "verification_status": row.verification_status,
        "remarks": row.remarks,
        "data_source": row.data_source,
    }


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def list_docs(self, *, project_id=None, parcel_id=None, proposal_id=None, page=1, page_size=20):
        stmt = select(Document)
        if project_id:
            stmt = stmt.where(Document.project_id == project_id)
        if parcel_id:
            stmt = stmt.where(Document.parcel_id == parcel_id)
        if proposal_id:
            stmt = stmt.where(Document.proposal_id == proposal_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(Document.uploaded_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return [_serialize(r) for r in rows], int(total)

    def get(self, doc_id: UUID) -> Document:
        row = self.db.get(Document, doc_id)
        if row is None:
            raise AppError(404, "NOT_FOUND", "Document not found")
        return row

    def get_dict(self, doc_id: UUID) -> dict:
        return _serialize(self.get(doc_id))

    def save_upload(
        self,
        user: User,
        *,
        filename: str,
        content: bytes,
        content_type: str | None,
        doc_type: str,
        name: str | None,
        project_id=None,
        parcel_id=None,
        proposal_id=None,
        acquisition_case_id=None,
    ) -> dict:
        if len(content) > MAX_UPLOAD_BYTES:
            raise AppError(400, "VALIDATION_ERROR", "File exceeds 10 MB limit")
        mime = content_type or "application/octet-stream"
        if mime not in ALLOWED_MIME:
            lower = (filename or "").lower()
            if lower.endswith(".pdf"):
                mime = "application/pdf"
            elif lower.endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            elif lower.endswith(".png"):
                mime = "image/png"
            elif lower.endswith(".webp"):
                mime = "image/webp"
        if mime not in ALLOWED_MIME:
            raise AppError(400, "VALIDATION_ERROR", "Unsupported file type")
        ext = ALLOWED_MIME[mime]
        public_id = f"DOC{uuid4().hex[:10].upper()}"
        dest_dir = UPLOAD_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4()}{ext}"
        path = dest_dir / stored_name
        path.write_bytes(content)
        row = Document(
            id=uuid4(),
            public_id=public_id,
            name=name or filename,
            doc_type=doc_type or "OTHER",
            project_id=project_id,
            parcel_id=parcel_id,
            proposal_id=proposal_id,
            acquisition_case_id=acquisition_case_id,
            storage_path=str(path),
            mime_type=mime,
            byte_size=len(content),
            uploaded_by=user.id,
            uploaded_at=datetime.now(timezone.utc),
            verification_status="PENDING",
            data_source="SYNTHETIC",
        )
        self.db.add(row)
        self.audit.record(user, "DOCUMENT_UPLOADED", "document", row.id, {"name": row.name})
        self.db.commit()
        return _serialize(row)

    def verify(self, user: User, doc_id: UUID, status: str, remarks: str | None) -> dict:
        if status not in ("VERIFIED", "REJECTED"):
            raise AppError(400, "VALIDATION_ERROR", "verification_status must be VERIFIED or REJECTED")
        row = self.get(doc_id)
        row.verification_status = status
        row.verified_by = user.id
        row.verified_at = datetime.now(timezone.utc)
        row.remarks = remarks
        self.audit.record(user, "DOCUMENT_VERIFIED", "document", row.id, {"status": status})
        self.db.commit()
        return _serialize(row)
