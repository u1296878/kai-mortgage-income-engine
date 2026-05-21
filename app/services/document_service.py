from pathlib import Path
from shutil import copyfileobj
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.config import settings
from app.exceptions import UnsupportedDocumentType
from app.models.document import Document
from app.models.document_type import DocumentType
from app.repositories import document_repo


def upload_document(db: Session, file: UploadFile, doc_type: str) -> Document:
    valid_doc_type = _validate_doc_type(doc_type)
    document_id = uuid4()
    storage_path = _save_upload_file(file, document_id)
    document = Document(
        id=str(document_id),
        filename=file.filename or "",
        doc_type=valid_doc_type.value,
        storage_path=str(storage_path),
    )
    saved_document = document_repo.save_document(db, document)
    log_event(
        "document_uploaded",
        {"document_id": saved_document.id, "doc_type": saved_document.doc_type},
    )
    return saved_document


def link_document_to_case(db: Session, document_id: UUID, case_id: UUID) -> Document:
    document = document_repo.get_document(db, document_id)
    document.case_id = str(case_id)
    saved_document = document_repo.save_document(db, document)
    log_event(
        "document_linked_to_case",
        {"document_id": saved_document.id, "case_id": saved_document.case_id},
    )
    return saved_document


def get_document(db: Session, document_id: UUID) -> Document:
    return document_repo.get_document(db, document_id)


def _validate_doc_type(doc_type: str | DocumentType) -> DocumentType:
    try:
        return DocumentType(doc_type)
    except ValueError as error:
        raise UnsupportedDocumentType(f"Unsupported document type: {doc_type}") from error


def _save_upload_file(file: UploadFile, document_id: UUID) -> Path:
    storage_root = Path(settings.storage_path)
    document_dir = storage_root / str(document_id)
    document_dir.mkdir(parents=True, exist_ok=True)
    storage_path = document_dir / (file.filename or "uploaded_document")
    file.file.seek(0)
    with storage_path.open("wb") as stored_file:
        copyfileobj(file.file, stored_file)
    return storage_path
