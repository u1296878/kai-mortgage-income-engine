from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions import CaseNotFound
from app.models.income_stream import IncomeStream
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import case_repo, income_stream_repo, result_repo
from app.schemas.income_stream_matching import IncomeStreamMatchSuggestion
from app.services import income_stream_service
from app.services.income_stream_match_rules import suggest_result_match


def preview_case_matches(
    db: Session,
    case_id: UUID,
    current_user: User,
    force_reassign: bool = False,
) -> list[IncomeStreamMatchSuggestion]:
    _get_accessible_case(db, case_id, current_user)
    results = _matchable_results(db, case_id, force_reassign)
    streams = income_stream_repo.list_income_streams_by_case(db, case_id)
    return [
        IncomeStreamMatchSuggestion.model_validate(suggest_result_match(result, streams))
        for result in results
    ]


def apply_case_matches(
    db: Session,
    case_id: UUID,
    current_user: User,
    force_reassign: bool = False,
) -> tuple[list[IncomeStreamMatchSuggestion], int, int]:
    suggestions = preview_case_matches(db, case_id, current_user, force_reassign)
    streams = income_stream_repo.list_income_streams_by_case(db, case_id)
    applied_count = 0
    created_stream_count = 0
    for suggestion in suggestions:
        if not suggestion.can_auto_apply:
            continue
        if suggestion.action == "assign_existing_stream" and suggestion.stream_id:
            income_stream_service.assign_result_to_stream(
                db,
                suggestion.stream_id,
                suggestion.result_id,
                current_user,
            )
            applied_count += 1
            continue
        if suggestion.action == "create_stream":
            stream = _find_stream(streams, suggestion)
            if stream is None:
                stream = income_stream_service.create_income_stream(
                    db,
                    case_id,
                    suggestion.suggested_stream_name,
                    suggestion.stream_type.value,
                    f"Auto-match: {suggestion.reason}",
                    current_user,
                )
                streams.append(stream)
                created_stream_count += 1
            income_stream_service.assign_result_to_stream(
                db,
                UUID(stream.id),
                suggestion.result_id,
                current_user,
            )
            applied_count += 1
    return suggestions, applied_count, created_stream_count


def _get_accessible_case(db: Session, case_id: UUID, current_user: User):
    case = case_repo.get_case(db, case_id)
    if not _is_manager(current_user) and case.broker_id != current_user.id:
        raise CaseNotFound(f"Case not found: {case_id}")
    return case


def _matchable_results(db: Session, case_id: UUID, force_reassign: bool) -> list:
    if force_reassign:
        return result_repo.list_results_by_case(db, case_id)
    return result_repo.list_unassigned_results_by_case(db, case_id)


def _find_stream(
    streams: list[IncomeStream],
    suggestion: IncomeStreamMatchSuggestion,
) -> IncomeStream | None:
    for stream in streams:
        if stream.stream_type == suggestion.stream_type.value and stream.name == suggestion.suggested_stream_name:
            return stream
    return None


def _is_manager(user: User) -> bool:
    return user.role == UserRole.manager.value
