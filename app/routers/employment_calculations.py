from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import (
    CaseNotFound,
    EmploymentCalculationNotFound,
    InvalidEmploymentInput,
)
from app.models.user import User
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
    current_user: Annotated[User, Depends(get_current_user)],
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
            current_user,
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[EmploymentCalculationResponse]:
    try:
        return employment_calculation_service.list_calculations_by_case(
            db,
            case_id,
            current_user,
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> EmploymentCalculationResponse:
    try:
        return employment_calculation_service.get_calculation(
            db,
            case_id,
            calc_id,
            current_user,
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        employment_calculation_service.delete_calculation(
            db,
            case_id,
            calc_id,
            current_user,
        )
    except (CaseNotFound, EmploymentCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)
