from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import FieldOps
from app.models.user import User
from app.schemas.common import clamp_page, envelope
from app.schemas.workflow import FieldPatch, RemarksBody
from app.services.documents import DocumentService
from app.services.field_verification import FieldVerificationService

router = APIRouter(prefix="/field-verification", tags=["Field Verification"])


@router.get("")
def list_verifications(
    user: User = Depends(FieldOps),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
):
    page, page_size = clamp_page(page, page_size)
    data, total = FieldVerificationService(db).list_rows(
        user, status=status, page=page, page_size=page_size
    )
    return envelope(data, page=page, page_size=page_size, total=total)


@router.get("/{rec_id}")
def get_verification(rec_id: UUID, user: User = Depends(FieldOps), db: Session = Depends(get_db)):
    return envelope(FieldVerificationService(db).get_dict(user, rec_id))


@router.patch("/{rec_id}")
def patch_verification(
    rec_id: UUID,
    body: FieldPatch,
    user: User = Depends(FieldOps),
    db: Session = Depends(get_db),
):
    return envelope(FieldVerificationService(db).update(user, rec_id, body))


@router.post("/{rec_id}/photos")
async def upload_photo(
    rec_id: UUID,
    user: User = Depends(FieldOps),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    rec = FieldVerificationService(db).get(user, rec_id)
    content = await file.read()
    data = DocumentService(db).save_upload(
        user,
        filename=file.filename or "photo.jpg",
        content=content,
        content_type=file.content_type,
        doc_type="PHOTO",
        name=file.filename,
        parcel_id=rec.parcel_id,
        acquisition_case_id=rec.acquisition_case_id,
    )
    return envelope(data)


@router.post("/{rec_id}/submit")
def submit_verification(
    rec_id: UUID,
    body: RemarksBody | None = None,
    user: User = Depends(FieldOps),
    db: Session = Depends(get_db),
):
    return envelope(
        FieldVerificationService(db).submit(user, rec_id, body.remarks if body else None)
    )
