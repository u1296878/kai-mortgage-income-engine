from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.models.case import Case
from app.repositories import case_repo, document_repo
from app.schemas.case import CaseResponse, CaseWithDocuments


def create_case(db: Session, title: str, broker_id: UUID) -> Case:
    case = Case(title=title, broker_id=str(broker_id))
    saved_case = case_repo.create_case(db, case)
    log_event(
        "case_created",
        {
            "case_id": saved_case.id,
            "broker_id": saved_case.broker_id,
            "title": saved_case.title,
        },
    )
    return saved_case


def get_case_with_documents(
    db: Session,
    case_id: UUID,
    broker_id: UUID | None = None,
) -> CaseWithDocuments:
    case = case_repo.get_case(db, case_id)
    documents = document_repo.list_documents_by_case(db, case_id, broker_id)
    case_data = CaseResponse.model_validate(case).model_dump()
    return CaseWithDocuments(
        **case_data,
        documents=documents,
    )


def update_case(db: Session, case_id: UUID, updates: dict) -> Case:
    update_values = _serialize_updates(updates)
    saved_case = case_repo.update_case(db, case_id, update_values)
    log_event("case_updated", {"case_id": saved_case.id, "updates": update_values})
    return saved_case


def list_cases(db: Session, broker_id: UUID | None = None) -> list[Case]:
    return case_repo.list_cases(db, broker_id)


def get_case(db: Session, case_id: UUID) -> Case:
    return case_repo.get_case(db, case_id)


def delete_case(db: Session, case_id: UUID) -> None:
    case_repo.delete_case(db, case_id)


def _serialize_updates(updates: dict) -> dict:
    return {
        field: value.value if isinstance(value, Enum) else value
        for field, value in updates.items()
    }
