from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.exceptions import (
    CaseNotFound,
    EmploymentCalculationNotFound,
    InvalidEmploymentInput,
)
from app.runtime.local_user import LOCAL_USER_ID
from app.schemas.income_inputs import EmploymentCalculationCreate, EmploymentInput
from app.schemas.income_results import EmploymentCalculationResponse
from app.services import employment_calculation_service

router = APIRouter(tags=["employment_calculations"])


@router.post(
    "/cases/{case_id}/employment-calculations",
    response_model=EmploymentCalculationResponse,
)
def create_employment_calculation(
    case_id: UUID,
    payload: EmploymentCalculationCreate,
    db: Annotated[Session, Depends(get_db)],
) -> EmploymentCalculationResponse:
    employment_input = EmploymentInput.model_validate(
        payload.model_dump(exclude={"borrower_id", "label"}),
    )
    try:
        return employment_calculation_service.create_calculation(
            db,
            case_id,
            employment_input,
            payload.borrower_id,
            payload.label,
            LOCAL_USER_ID,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidEmploymentInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "/cases/{case_id}/employment-calculations",
    response_model=list[EmploymentCalculationResponse],
)
def list_employment_calculations(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[EmploymentCalculationResponse]:
    try:
        return employment_calculation_service.list_calculations_by_case(
            db,
            case_id,
            LOCAL_USER_ID,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get(
    "/cases/{case_id}/employment-calculations/{calc_id}",
    response_model=EmploymentCalculationResponse,
)
def get_employment_calculation(
    case_id: UUID,
    calc_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> EmploymentCalculationResponse:
    try:
        return employment_calculation_service.get_calculation(
            db,
            case_id,
            calc_id,
            LOCAL_USER_ID,
        )
    except (CaseNotFound, EmploymentCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete(
    "/cases/{case_id}/employment-calculations/{calc_id}",
    status_code=204,
)
def delete_employment_calculation(
    case_id: UUID,
    calc_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        employment_calculation_service.delete_calculation(
            db,
            case_id,
            calc_id,
            LOCAL_USER_ID,
        )
    except (CaseNotFound, EmploymentCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)
