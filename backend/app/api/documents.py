from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AnyReader, OfficerOps
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.schemas.workflow import DocumentVerify
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("")
def list_documents(
    user: User = Depends(AnyReader),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_id: UUID | None = None,
    parcel_id: UUID | None = None,
    proposal_id: UUID | None = None,
):
    page, page_size = clamp_page(page, page_size)
    data, total = DocumentService(db).list_docs(
        project_id=project_id,
        parcel_id=parcel_id,
        proposal_id=proposal_id,
        page=page,
        page_size=page_size,
    )
    return envelope(data, page=page, page_size=page_size, total=total)


@router.get("/{doc_id}")
def get_document(doc_id: UUID, user: User = Depends(AnyReader), db: Session = Depends(get_db)):
    return envelope(DocumentService(db).get_dict(doc_id))


@router.post("", status_code=201)
async def upload_document(
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    doc_type: str = Form(default="OTHER"),
    project_id: UUID | None = Form(default=None),
    parcel_id: UUID | None = Form(default=None),
    proposal_id: UUID | None = Form(default=None),
    acquisition_case_id: UUID | None = Form(default=None),
):
    content = await file.read()
    data = DocumentService(db).save_upload(
        user,
        filename=file.filename or "upload.bin",
        content=content,
        content_type=file.content_type,
        doc_type=doc_type,
        name=name,
        project_id=project_id,
        parcel_id=parcel_id,
        proposal_id=proposal_id,
        acquisition_case_id=acquisition_case_id,
    )
    return envelope(data)


@router.patch("/{doc_id}")
def verify_document(
    doc_id: UUID,
    body: DocumentVerify,
    user: User = Depends(OfficerOps),
    db: Session = Depends(get_db),
):
    return envelope(DocumentService(db).verify(user, doc_id, body.verification_status, body.remarks))
