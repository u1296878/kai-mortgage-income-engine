from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions import (
    BorrowerNotFound,
    CaseNotFound,
    IncomeStreamNotFound,
    InvalidBorrowerAssignment,
)
from app.models.borrower import Borrower
from app.models.income_stream import IncomeStream
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import borrower_repo, case_repo, income_stream_repo


def create_borrower(
    db: Session,
    case_id: UUID,
    first_name: str,
    last_name: str,
    role: str,
    current_user: User,
) -> Borrower:
    case = _get_accessible_case(db, case_id, current_user)
    borrower = Borrower(
        case_id=case.id,
        broker_id=case.broker_id,
        first_name=first_name,
        last_name=last_name,
        role=role,
    )
    return borrower_repo.create_borrower(db, borrower)


def list_borrowers_by_case(
    db: Session,
    case_id: UUID,
    current_user: User,
) -> list[Borrower]:
    _get_accessible_case(db, case_id, current_user)
    return borrower_repo.list_borrowers_by_case(db, case_id)


def get_borrower(db: Session, borrower_id: UUID, current_user: User) -> Borrower:
    return _get_accessible_borrower(db, borrower_id, current_user)


def update_borrower(
    db: Session,
    borrower_id: UUID,
    updates: dict,
    current_user: User,
) -> Borrower:
    _get_accessible_borrower(db, borrower_id, current_user)
    update_values = _serialize_updates(updates)
    return borrower_repo.update_borrower(db, borrower_id, update_values)


def delete_borrower(db: Session, borrower_id: UUID, current_user: User) -> None:
    borrower = _get_accessible_borrower(db, borrower_id, current_user)
    assigned_streams = income_stream_repo.list_income_streams_by_borrower(db, borrower_id)
    cleared_streams: list[str] = []
    try:
        for stream in assigned_streams:
            income_stream_repo.update_income_stream_borrower(db, UUID(stream.id), None)
            cleared_streams.append(stream.id)
        borrower_repo.delete_borrower(db, borrower_id)
    except Exception as error:
        failed_streams = _restore_borrower_assignments(db, borrower_id, cleared_streams)
        message = (
            "Borrower deletion failed after stream updates; original assignments were restored"
        )
        if failed_streams:
            message = (
                "Borrower deletion failed and some stream assignments could not be restored: "
                + ", ".join(failed_streams)
            )
        raise InvalidBorrowerAssignment(
            message,
        ) from error


def assign_income_stream_to_borrower(
    db: Session,
    borrower_id: UUID,
    stream_id: UUID,
    current_user: User,
) -> IncomeStream:
    borrower = _get_accessible_borrower(db, borrower_id, current_user)
    stream = _get_accessible_stream(db, stream_id, current_user)
    _validate_same_case(borrower, stream)
    return income_stream_repo.update_income_stream_borrower(db, stream_id, borrower_id)


def clear_income_stream_borrower(
    db: Session,
    borrower_id: UUID,
    stream_id: UUID,
    current_user: User,
) -> IncomeStream:
    borrower = _get_accessible_borrower(db, borrower_id, current_user)
    stream = _get_accessible_stream(db, stream_id, current_user)
    _validate_same_case(borrower, stream)
    if stream.borrower_id != str(borrower_id):
        raise InvalidBorrowerAssignment("Income stream is not assigned to this borrower")
    return income_stream_repo.update_income_stream_borrower(db, stream_id, None)


def _restore_borrower_assignments(
    db: Session,
    borrower_id: UUID,
    stream_ids: list[str],
) -> list[str]:
    failed_streams: list[str] = []
    for stream_id in stream_ids:
        try:
            income_stream_repo.update_income_stream_borrower(db, UUID(stream_id), borrower_id)
        except Exception:
            failed_streams.append(stream_id)
    return failed_streams


def _get_accessible_case(db: Session, case_id: UUID, current_user: User):
    case = case_repo.get_case(db, case_id)
    if not _is_manager(current_user) and case.broker_id != current_user.id:
        raise CaseNotFound(f"Case not found: {case_id}")
    return case


def _get_accessible_borrower(
    db: Session,
    borrower_id: UUID,
    current_user: User,
) -> Borrower:
    borrower = borrower_repo.get_borrower(db, borrower_id)
    if not _is_manager(current_user) and borrower.broker_id != current_user.id:
        raise BorrowerNotFound(f"Borrower not found: {borrower_id}")
    return borrower


def _get_accessible_stream(db: Session, stream_id: UUID, current_user: User) -> IncomeStream:
    stream = income_stream_repo.get_income_stream(db, stream_id)
    if not _is_manager(current_user) and stream.broker_id != current_user.id:
        raise IncomeStreamNotFound(f"Income stream not found: {stream_id}")
    return stream


def _validate_same_case(borrower: Borrower, stream: IncomeStream) -> None:
    if borrower.case_id != stream.case_id:
        raise InvalidBorrowerAssignment(
            "Borrower and income stream must belong to the same case",
        )


def _serialize_updates(updates: dict) -> dict:
    return {
        field: value.value if isinstance(value, Enum) else value
        for field, value in updates.items()
    }


def _is_manager(user: User) -> bool:
    return user.role == UserRole.manager.value
