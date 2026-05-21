from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.exceptions import DocumentNotFound
from app.models.document_type import DocumentType
from app.schemas.document import DocumentCaseLink, DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: Annotated[UploadFile, File()],
    doc_type: Annotated[DocumentType, Form()],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentResponse:
    return document_service.upload_document(db, file, doc_type)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> DocumentResponse:
    try:
        return document_service.get_document(db, document_id)
    except DocumentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/{document_id}/case", response_model=DocumentResponse)
def link_document_to_case(
    document_id: UUID,
    link: DocumentCaseLink,
    db: Annotated[Session, Depends(get_db)],
) -> DocumentResponse:
    try:
        return document_service.link_document_to_case(db, document_id, link.case_id)
    except DocumentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
