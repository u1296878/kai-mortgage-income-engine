from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.exceptions import (
    BorrowerNotFound,
    CaseNotFound,
    IncomeStreamNotFound,
    InvalidBorrowerAssignment,
)
from app.runtime.local_user import LOCAL_USER_ID
from app.schemas.borrower import BorrowerCreate, BorrowerResponse, BorrowerUpdate
from app.schemas.income_stream import IncomeStreamResponse
from app.services import borrower_service

router = APIRouter(tags=["borrowers"])


@router.post("/cases/{case_id}/borrowers", response_model=BorrowerResponse)
def create_borrower(
    case_id: UUID,
    payload: BorrowerCreate,
    db: Annotated[Session, Depends(get_db)],
) -> BorrowerResponse:
    try:
        return borrower_service.create_borrower(
            db,
            case_id,
            payload.first_name,
            payload.last_name,
            payload.role,
            LOCAL_USER_ID,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/cases/{case_id}/borrowers", response_model=list[BorrowerResponse])
def list_borrowers(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[BorrowerResponse]:
    try:
        return borrower_service.list_borrowers_by_case(db, case_id, LOCAL_USER_ID)
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/borrowers/{borrower_id}", response_model=BorrowerResponse)
def get_borrower(
    borrower_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> BorrowerResponse:
    try:
        return borrower_service.get_borrower(db, borrower_id, LOCAL_USER_ID)
    except BorrowerNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/borrowers/{borrower_id}", response_model=BorrowerResponse)
def update_borrower(
    borrower_id: UUID,
    payload: BorrowerUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> BorrowerResponse:
    try:
        updates = payload.model_dump(exclude_none=True)
        return borrower_service.update_borrower(db, borrower_id, updates, LOCAL_USER_ID)
    except BorrowerNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/borrowers/{borrower_id}", status_code=204)
def delete_borrower(
    borrower_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        borrower_service.delete_borrower(db, borrower_id, LOCAL_USER_ID)
    except BorrowerNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidBorrowerAssignment as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return Response(status_code=204)


@router.post(
    "/borrowers/{borrower_id}/income-streams/{stream_id}",
    response_model=IncomeStreamResponse,
)
def assign_income_stream_to_borrower(
    borrower_id: UUID,
    stream_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> IncomeStreamResponse:
    try:
        return borrower_service.assign_income_stream_to_borrower(
            db,
            borrower_id,
            stream_id,
            LOCAL_USER_ID,
        )
    except (BorrowerNotFound, IncomeStreamNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidBorrowerAssignment as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete(
    "/borrowers/{borrower_id}/income-streams/{stream_id}",
    response_model=IncomeStreamResponse,
)
def clear_income_stream_borrower(
    borrower_id: UUID,
    stream_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> IncomeStreamResponse:
    try:
        return borrower_service.clear_income_stream_borrower(
            db,
            borrower_id,
            stream_id,
            LOCAL_USER_ID,
        )
    except (BorrowerNotFound, IncomeStreamNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidBorrowerAssignment as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
