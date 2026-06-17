from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.models.case import Case
from app.repositories import borrower_repo, case_repo, document_repo, income_stream_repo
from app.services import document_service
from app.schemas.case import CaseResponse, CaseWithDocuments


def create_case(db: Session, title: str) -> Case:
    case = Case(title=title)
    saved_case = case_repo.create_case(db, case)
    log_event(
        "case_created",
        {
            "case_id": saved_case.id,
            "title": saved_case.title,
        },
    )
    return saved_case


def get_case_with_documents(
    db: Session,
    case_id: UUID,
) -> CaseWithDocuments:
    case = case_repo.get_case(db, case_id)
    documents = document_repo.list_documents_by_case(db, case_id)
    case_data = CaseResponse.model_validate(case).model_dump()
    return CaseWithDocuments(
        **case_data,
        documents=documents,
    )


def update_case(
    db: Session,
    case_id: UUID,
    updates: dict,
) -> Case:
    case_repo.get_case(db, case_id)
    update_values = _serialize_updates(updates)
    saved_case = case_repo.update_case(db, case_id, update_values)
    log_event("case_updated", {"case_id": saved_case.id, "updates": update_values})
    return saved_case


def list_cases(db: Session) -> list[Case]:
    return case_repo.list_cases(db)


def get_case(db: Session, case_id: UUID) -> Case:
    return case_repo.get_case(db, case_id)


def delete_case(db: Session, case_id: UUID) -> None:
    case_repo.get_case(db, case_id)
    for document in document_repo.list_documents_by_case(db, case_id):
        document_service.delete_document(db, UUID(document.id))
    for stream in income_stream_repo.list_income_streams_by_case(db, case_id):
        income_stream_repo.delete_income_stream(db, UUID(stream.id))
    for borrower in borrower_repo.list_borrowers_by_case(db, case_id):
        borrower_repo.delete_borrower(db, UUID(borrower.id))
    case_repo.delete_case(db, case_id)


def _serialize_updates(updates: dict) -> dict:
    return {
        field: value.value if isinstance(value, Enum) else value
        for field, value in updates.items()
    }
