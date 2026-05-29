from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import (
    CaseNotFound,
    IncomeStreamNotFound,
    InvalidIncomeStreamAssignment,
    ResultNotFound,
)
from app.models.user import User
from app.schemas.income_stream import (
    IncomeStreamCreate,
    IncomeStreamResponse,
    IncomeStreamUpdate,
)
from app.services import income_stream_service

router = APIRouter(tags=["income_streams"])


@router.post("/cases/{case_id}/income-streams", response_model=IncomeStreamResponse)
def create_income_stream(
    case_id: UUID,
    payload: IncomeStreamCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> IncomeStreamResponse:
    try:
        return income_stream_service.create_income_stream(
            db,
            case_id,
            payload.name,
            payload.stream_type,
            payload.notes,
            current_user,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/cases/{case_id}/income-streams", response_model=list[IncomeStreamResponse])
def list_income_streams(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[IncomeStreamResponse]:
    try:
        return income_stream_service.list_income_streams_by_case(db, case_id, current_user)
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/income-streams/{stream_id}", response_model=IncomeStreamResponse)
def get_income_stream(
    stream_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> IncomeStreamResponse:
    try:
        return income_stream_service.get_income_stream(db, stream_id, current_user)
    except IncomeStreamNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/income-streams/{stream_id}", response_model=IncomeStreamResponse)
def update_income_stream(
    stream_id: UUID,
    payload: IncomeStreamUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> IncomeStreamResponse:
    try:
        updates = payload.model_dump(exclude_none=True)
        return income_stream_service.update_income_stream(db, stream_id, updates, current_user)
    except IncomeStreamNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/income-streams/{stream_id}", status_code=204)
def delete_income_stream(
    stream_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        income_stream_service.delete_income_stream(db, stream_id, current_user)
    except IncomeStreamNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)


@router.post(
    "/income-streams/{stream_id}/results/{result_id}",
    response_model=IncomeStreamResponse,
)
def assign_result_to_stream(
    stream_id: UUID,
    result_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> IncomeStreamResponse:
    try:
        return income_stream_service.assign_result_to_stream(
            db,
            stream_id,
            result_id,
            current_user,
        )
    except (IncomeStreamNotFound, ResultNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidIncomeStreamAssignment as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete(
    "/income-streams/{stream_id}/results/{result_id}",
    response_model=IncomeStreamResponse,
)
def unassign_result_from_stream(
    stream_id: UUID,
    result_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> IncomeStreamResponse:
    try:
        return income_stream_service.unassign_result_from_stream(
            db,
            stream_id,
            result_id,
            current_user,
        )
    except (IncomeStreamNotFound, ResultNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidIncomeStreamAssignment as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
