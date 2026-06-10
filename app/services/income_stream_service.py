from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions import (
    CaseNotFound,
    IncomeStreamNotFound,
    InvalidIncomeStreamAssignment,
    ResultNotFound,
)
from app.models.income_stream import IncomeStream
from app.models.result import Result
from app.repositories import case_repo, income_stream_repo, result_repo
from app.services import income_service


def create_income_stream(
    db: Session,
    case_id: UUID,
    name: str,
    stream_type: str,
    notes: str | None,
    local_user_id: UUID,
) -> IncomeStream:
    case = _get_accessible_case(db, case_id, local_user_id)
    stream = IncomeStream(
        case_id=case.id,
        broker_id=case.broker_id,
        name=name,
        stream_type=stream_type,
        notes=notes,
    )
    return income_stream_repo.create_income_stream(db, stream)


def list_income_streams_by_case(
    db: Session,
    case_id: UUID,
    local_user_id: UUID,
) -> list[IncomeStream]:
    _get_accessible_case(db, case_id, local_user_id)
    return income_stream_repo.list_income_streams_by_case(db, case_id)


def get_income_stream(
    db: Session,
    stream_id: UUID,
    local_user_id: UUID,
) -> IncomeStream:
    return _get_accessible_stream(db, stream_id, local_user_id)


def update_income_stream(
    db: Session,
    stream_id: UUID,
    updates: dict,
    local_user_id: UUID,
) -> IncomeStream:
    _get_accessible_stream(db, stream_id, local_user_id)
    update_values = _serialize_updates(updates)
    return income_stream_repo.update_income_stream(db, stream_id, update_values)


def delete_income_stream(db: Session, stream_id: UUID, local_user_id: UUID) -> None:
    _get_accessible_stream(db, stream_id, local_user_id)
    result_repo.clear_income_stream_assignments(db, stream_id)
    income_stream_repo.delete_income_stream(db, stream_id)


def assign_result_to_stream(
    db: Session,
    stream_id: UUID,
    result_id: UUID,
    local_user_id: UUID,
) -> IncomeStream:
    stream = _get_accessible_stream(db, stream_id, local_user_id)
    result = _get_accessible_result(db, result_id, local_user_id)
    _validate_stream_result_case(stream, result)
    result_repo.assign_result_to_income_stream(db, result_id, stream_id)
    return recalculate_income_stream(db, stream_id)


def unassign_result_from_stream(
    db: Session,
    stream_id: UUID,
    result_id: UUID,
    local_user_id: UUID,
) -> IncomeStream:
    stream = _get_accessible_stream(db, stream_id, local_user_id)
    result = _get_accessible_result(db, result_id, local_user_id)
    _validate_stream_result_case(stream, result)
    if result.income_stream_id != str(stream_id):
        raise InvalidIncomeStreamAssignment(
            "Result is not assigned to this income stream",
        )
    result_repo.clear_result_income_stream(db, result_id)
    return recalculate_income_stream(db, stream_id)


def recalculate_income_stream(db: Session, stream_id: UUID) -> IncomeStream:
    stream_results = result_repo.list_results_by_income_stream(db, stream_id)
    annual_income, confidence = income_service.stream_income_snapshot(stream_results)
    return income_stream_repo.update_income_stream(
        db,
        stream_id,
        {"annual_income": annual_income, "confidence": confidence},
    )


def _get_accessible_case(db: Session, case_id: UUID, local_user_id: UUID):
    case = case_repo.get_case(db, case_id)
    # TODO step 2b: remove ownership plumbing.
    if case.broker_id != str(local_user_id):
        raise CaseNotFound(f"Case not found: {case_id}")
    return case


def _get_accessible_stream(
    db: Session,
    stream_id: UUID,
    local_user_id: UUID,
) -> IncomeStream:
    stream = income_stream_repo.get_income_stream(db, stream_id)
    # TODO step 2b: remove ownership plumbing.
    if stream.broker_id != str(local_user_id):
        raise IncomeStreamNotFound(f"Income stream not found: {stream_id}")
    return stream


def _get_accessible_result(db: Session, result_id: UUID, local_user_id: UUID) -> Result:
    result = result_repo.get_result(db, result_id)
    if result.case_id is None:
        raise InvalidIncomeStreamAssignment("Result must be linked to a case")
    case = case_repo.get_case(db, UUID(result.case_id))
    # TODO step 2b: remove ownership plumbing.
    if case.broker_id != str(local_user_id):
        raise ResultNotFound(f"Result not found: {result_id}")
    return result


def _validate_stream_result_case(stream: IncomeStream, result: Result) -> None:
    if result.case_id != stream.case_id:
        raise InvalidIncomeStreamAssignment(
            "Result and income stream must belong to the same case",
        )


def _serialize_updates(updates: dict) -> dict:
    return {
        field: value.value if isinstance(value, Enum) else value
        for field, value in updates.items()
    }
