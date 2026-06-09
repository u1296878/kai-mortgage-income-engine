from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import (
    CaseNotFound,
    InvalidSelfEmploymentInput,
    SelfEmploymentCalculationNotFound,
)
from app.models.user import User
from app.schemas.self_employment_results import (
    SelfEmploymentCalculationCreate,
    SelfEmploymentCalculationResponse,
    SelfEmploymentCalculationUpdate,
)
from app.services import self_employment_calculation_service

router = APIRouter(tags=["self_employment_calculations"])


@router.post(
    "/cases/{case_id}/self-employment-calculations",
    response_model=SelfEmploymentCalculationResponse,
)
def create_self_employment_calculation(
    case_id: UUID,
    payload: SelfEmploymentCalculationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SelfEmploymentCalculationResponse:
    try:
        return self_employment_calculation_service.create_calculation(
            db, case_id, payload, current_user
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidSelfEmploymentInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "/cases/{case_id}/self-employment-calculations",
    response_model=list[SelfEmploymentCalculationResponse],
)
def list_self_employment_calculations(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[SelfEmploymentCalculationResponse]:
    try:
        return self_employment_calculation_service.list_calculations_by_case(
            db, case_id, current_user
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get(
    "/cases/{case_id}/self-employment-calculations/{calc_id}",
    response_model=SelfEmploymentCalculationResponse,
)
def get_self_employment_calculation(
    case_id: UUID,
    calc_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SelfEmploymentCalculationResponse:
    try:
        return self_employment_calculation_service.get_calculation(
            db, case_id, calc_id, current_user
        )
    except (CaseNotFound, SelfEmploymentCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch(
    "/cases/{case_id}/self-employment-calculations/{calc_id}",
    response_model=SelfEmploymentCalculationResponse,
)
def update_self_employment_calculation(
    case_id: UUID,
    calc_id: UUID,
    payload: SelfEmploymentCalculationUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SelfEmploymentCalculationResponse:
    try:
        return self_employment_calculation_service.update_calculation(
            db, case_id, calc_id, payload, current_user
        )
    except (CaseNotFound, SelfEmploymentCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete(
    "/cases/{case_id}/self-employment-calculations/{calc_id}",
    status_code=204,
)
def delete_self_employment_calculation(
    case_id: UUID,
    calc_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        self_employment_calculation_service.delete_calculation(
            db, case_id, calc_id, current_user
        )
    except (CaseNotFound, SelfEmploymentCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)
