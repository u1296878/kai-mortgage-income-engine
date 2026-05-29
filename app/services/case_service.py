from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import CaseNotFound, InvalidCaseRequest
from app.models.case import Case
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import case_repo, document_repo
from app.schemas.case import CaseResponse, CaseWithDocuments


def create_case(
    db: Session,
    title: str,
    broker_id: UUID | None,
    current_user: User,
) -> Case:
    case = Case(title=title, broker_id=_case_owner_id(broker_id, current_user))
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
    current_user: User,
    broker_id: UUID | None = None,
) -> CaseWithDocuments:
    case = _get_accessible_case(db, case_id, current_user)
    scoped_broker_id = broker_id if _is_manager(current_user) else UUID(current_user.id)
    documents = document_repo.list_documents_by_case(
        db,
        case_id,
        scoped_broker_id,
    )
    case_data = CaseResponse.model_validate(case).model_dump()
    return CaseWithDocuments(
        **case_data,
        documents=documents,
    )


def update_case(
    db: Session,
    case_id: UUID,
    updates: dict,
    current_user: User,
) -> Case:
    _get_accessible_case(db, case_id, current_user)
    update_values = _serialize_updates(updates)
    saved_case = case_repo.update_case(db, case_id, update_values)
    log_event("case_updated", {"case_id": saved_case.id, "updates": update_values})
    return saved_case


def list_cases(
    db: Session,
    current_user: User,
    broker_id: UUID | None = None,
) -> list[Case]:
    if _is_manager(current_user):
        return case_repo.list_cases(db, broker_id)
    return case_repo.list_cases(db, UUID(current_user.id))


def get_case(db: Session, case_id: UUID, current_user: User) -> Case:
    return _get_accessible_case(db, case_id, current_user)


def delete_case(db: Session, case_id: UUID, current_user: User) -> None:
    _get_accessible_case(db, case_id, current_user)
    case_repo.delete_case(db, case_id)


def _serialize_updates(updates: dict) -> dict:
    return {
        field: value.value if isinstance(value, Enum) else value
        for field, value in updates.items()
    }


def _case_owner_id(broker_id: UUID | None, current_user: User) -> str:
    if _is_manager(current_user):
        if broker_id is None:
            raise InvalidCaseRequest("Manager case creation requires broker_id")
        return str(broker_id)
    return current_user.id


def _get_accessible_case(db: Session, case_id: UUID, current_user: User) -> Case:
    case = case_repo.get_case(db, case_id)
    if not _is_manager(current_user) and case.broker_id != current_user.id:
        raise CaseNotFound(f"Case not found: {case_id}")
    return case


def _is_manager(user: User) -> bool:
    return user.role == UserRole.manager.value
