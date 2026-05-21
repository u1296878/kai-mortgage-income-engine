from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.exceptions import ResultNotFound
from app.schemas.result import CaseSummaryResponse, ResultResponse
from app.services import result_service

router = APIRouter(tags=["results"])


@router.get("/results/{result_id}", response_model=ResultResponse)
def get_result(
    result_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> ResultResponse:
    try:
        return result_service.get_result(db, result_id)
    except ResultNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/jobs/{job_id}/result", response_model=ResultResponse)
def get_job_result(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> ResultResponse:
    try:
        return result_service.get_result_for_job(db, job_id)
    except ResultNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/cases/{case_id}/summary", response_model=CaseSummaryResponse)
def get_case_summary(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CaseSummaryResponse:
    return result_service.get_case_summary(db, case_id)
