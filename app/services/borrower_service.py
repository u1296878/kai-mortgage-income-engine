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
from app.repositories import borrower_repo, case_repo, income_stream_repo


def create_borrower(
    db: Session,
    case_id: UUID,
    first_name: str,
    last_name: str,
    role: str,
    local_user_id: UUID,
) -> Borrower:
    case = _get_accessible_case(db, case_id, local_user_id)
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
    local_user_id: UUID,
) -> list[Borrower]:
    _get_accessible_case(db, case_id, local_user_id)
    return borrower_repo.list_borrowers_by_case(db, case_id)


def get_borrower(db: Session, borrower_id: UUID, local_user_id: UUID) -> Borrower:
    return _get_accessible_borrower(db, borrower_id, local_user_id)


def update_borrower(
    db: Session,
    borrower_id: UUID,
    updates: dict,
    local_user_id: UUID,
) -> Borrower:
    _get_accessible_borrower(db, borrower_id, local_user_id)
    update_values = _serialize_updates(updates)
    return borrower_repo.update_borrower(db, borrower_id, update_values)


def delete_borrower(db: Session, borrower_id: UUID, local_user_id: UUID) -> None:
    borrower = _get_accessible_borrower(db, borrower_id, local_user_id)
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
    local_user_id: UUID,
) -> IncomeStream:
    borrower = _get_accessible_borrower(db, borrower_id, local_user_id)
    stream = _get_accessible_stream(db, stream_id, local_user_id)
    _validate_same_case(borrower, stream)
    return income_stream_repo.update_income_stream_borrower(db, stream_id, borrower_id)


def clear_income_stream_borrower(
    db: Session,
    borrower_id: UUID,
    stream_id: UUID,
    local_user_id: UUID,
) -> IncomeStream:
    borrower = _get_accessible_borrower(db, borrower_id, local_user_id)
    stream = _get_accessible_stream(db, stream_id, local_user_id)
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


def _get_accessible_case(db: Session, case_id: UUID, local_user_id: UUID):
    case = case_repo.get_case(db, case_id)
    # TODO step 2b: remove ownership plumbing.
    if case.broker_id != str(local_user_id):
        raise CaseNotFound(f"Case not found: {case_id}")
    return case


def _get_accessible_borrower(
    db: Session,
    borrower_id: UUID,
    local_user_id: UUID,
) -> Borrower:
    borrower = borrower_repo.get_borrower(db, borrower_id)
    # TODO step 2b: remove ownership plumbing.
    if borrower.broker_id != str(local_user_id):
        raise BorrowerNotFound(f"Borrower not found: {borrower_id}")
    return borrower


def _get_accessible_stream(db: Session, stream_id: UUID, local_user_id: UUID) -> IncomeStream:
    stream = income_stream_repo.get_income_stream(db, stream_id)
    # TODO step 2b: remove ownership plumbing.
    if stream.broker_id != str(local_user_id):
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
