import mimetypes
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import DocumentNotFound, Unauthorized
from app.models.document_type import DocumentType
from app.models.user import User
from app.schemas.document import DocumentCaseLink, DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: Annotated[UploadFile, File()],
    doc_type: Annotated[DocumentType, Form()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    case_id: Annotated[UUID | None, Form()] = None,
) -> DocumentResponse:
    try:
        return document_service.upload_document(db, file, doc_type, current_user, case_id)
    except DocumentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentResponse:
    try:
        return document_service.get_document(db, document_id, current_user)
    except DocumentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{document_id}/file")
def get_document_file(
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    try:
        document, file_path = document_service.get_document_file(db, document_id, current_user)
    except DocumentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Unauthorized as error:
        raise HTTPException(status_code=403, detail=str(error)) from error

    content_type, _ = mimetypes.guess_type(document.filename)
    return StreamingResponse(
        _iter_file(file_path),
        media_type=content_type or "application/octet-stream",
    )


@router.patch("/{document_id}/case", response_model=DocumentResponse)
def link_document_to_case(
    document_id: UUID,
    link: DocumentCaseLink,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentResponse:
    try:
        return document_service.link_document_to_case(
            db,
            document_id,
            link.case_id,
            current_user,
        )
    except DocumentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def _iter_file(file_path: Path):
    with file_path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 64):
            yield chunk
