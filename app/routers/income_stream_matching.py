from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.exceptions import CaseNotFound
from app.runtime.local_user import LOCAL_USER_ID
from app.schemas.income_stream_matching import (
    IncomeStreamMatchApplyRequest,
    IncomeStreamMatchApplyResponse,
    IncomeStreamMatchSuggestion,
)
from app.services import income_stream_match_service

router = APIRouter(tags=["income_stream_matching"])


@router.get(
    "/cases/{case_id}/income-stream-matches",
    response_model=list[IncomeStreamMatchSuggestion],
)
def preview_case_matches(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[IncomeStreamMatchSuggestion]:
    try:
        return income_stream_match_service.preview_case_matches(db, case_id, LOCAL_USER_ID)
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post(
    "/cases/{case_id}/income-stream-matches/apply",
    response_model=IncomeStreamMatchApplyResponse,
)
def apply_case_matches(
    case_id: UUID,
    payload: IncomeStreamMatchApplyRequest,
    db: Annotated[Session, Depends(get_db)],
) -> IncomeStreamMatchApplyResponse:
    try:
        suggestions, applied_count, created_stream_count = income_stream_match_service.apply_case_matches(
            db,
            case_id,
            LOCAL_USER_ID,
            payload.force_reassign,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return IncomeStreamMatchApplyResponse(
        suggestions=suggestions,
        applied_count=applied_count,
        created_stream_count=created_stream_count,
    )
