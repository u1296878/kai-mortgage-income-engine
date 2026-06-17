from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import CaseNotFound, DocumentNotFound, UnsupportedDocumentType
from app.models.document import Document
from app.models.document_type import DocumentType
from app.repositories import case_repo, document_repo, job_repo, result_repo
from app.services import job_service
from app.storage import storage


def upload_document(
    db: Session,
    file: UploadFile,
    doc_type: str,
    case_id: UUID | None = None,
) -> Document:
    valid_doc_type = _validate_doc_type(doc_type)
    document_id = uuid4()
    storage_path = storage.save_document_file(file.file, document_id)
    document = Document(
        id=str(document_id),
        filename=file.filename or "",
        doc_type=valid_doc_type.value,
        storage_path=str(storage_path),
    )
    if case_id is not None:
        _set_document_case(db, document, case_id)
    saved_document = document_repo.save_document(db, document)
    job_service.create_job_for_document(db, saved_document.id)
    log_event(
        "document_uploaded",
        {"document_id": saved_document.id, "doc_type": saved_document.doc_type},
    )
    return saved_document


def link_document_to_case(
    db: Session,
    document_id: UUID,
    case_id: UUID,
) -> Document:
    document = document_repo.get_document(db, document_id)
    _set_document_case(db, document, case_id)
    saved_document = document_repo.save_document(db, document)
    log_event(
        "document_linked_to_case",
        {
            "document_id": saved_document.id,
            "case_id": saved_document.case_id,
        },
    )
    return saved_document


def unlink_document_from_case(
    db: Session,
    document_id: UUID,
) -> Document:
    document = get_document(db, document_id)
    document.case_id = None
    saved_document = document_repo.save_document(db, document)
    result_repo.clear_case_for_document(db, document_id)
    log_event("document_unlinked_from_case", {"document_id": saved_document.id})
    return saved_document


def delete_document(db: Session, document_id: UUID) -> None:
    document = get_document(db, document_id)
    result_repo.delete_results_by_document(db, document_id)
    job_repo.delete_job_by_document(db, document_id)
    document_repo.delete_document(db, document_id)
    storage.delete_document_file(UUID(document.id))
    log_event("document_deleted", {"document_id": document.id})


def get_document(db: Session, document_id: UUID) -> Document:
    return document_repo.get_document(db, document_id)


def get_document_file(
    db: Session,
    document_id: UUID,
) -> tuple[Document, Path]:
    document = document_repo.get_document(db, document_id)
    file_path = storage.get_document_path(document_id)
    if not file_path.exists():
        raise DocumentNotFound(f"Document not found: {document_id}")
    return document, file_path


def _validate_doc_type(doc_type: str | DocumentType) -> DocumentType:
    try:
        return DocumentType(doc_type)
    except ValueError as error:
        raise UnsupportedDocumentType(f"Unsupported document type: {doc_type}") from error


def _set_document_case(
    db: Session,
    document: Document,
    case_id: UUID,
) -> None:
    try:
        case_repo.get_case(db, case_id)
    except CaseNotFound as error:
        raise DocumentNotFound(f"Document not found: {document.id}") from error

    document.case_id = str(case_id)
