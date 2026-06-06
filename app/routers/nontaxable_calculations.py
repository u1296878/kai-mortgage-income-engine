from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import (
    CaseNotFound,
    InvalidNonTaxableInput,
    NonTaxableCalculationNotFound,
)
from app.models.user import User
from app.schemas.nontaxable_inputs import NonTaxableCalculationCreate
from app.schemas.nontaxable_results import NonTaxableCalculationResponse
from app.services import nontaxable_calculation_service

router = APIRouter(tags=["nontaxable_calculations"])


@router.post(
    "/cases/{case_id}/nontaxable-calculations",
    response_model=NonTaxableCalculationResponse,
)
def create_nontaxable_calculation(
    case_id: UUID,
    payload: NonTaxableCalculationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NonTaxableCalculationResponse:
    try:
        return nontaxable_calculation_service.create_calculation(
            db, case_id, payload, current_user
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidNonTaxableInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "/cases/{case_id}/nontaxable-calculations",
    response_model=list[NonTaxableCalculationResponse],
)
def list_nontaxable_calculations(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[NonTaxableCalculationResponse]:
    try:
        return nontaxable_calculation_service.list_calculations_by_case(
            db, case_id, current_user
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get(
    "/cases/{case_id}/nontaxable-calculations/{calc_id}",
    response_model=NonTaxableCalculationResponse,
)
def get_nontaxable_calculation(
    case_id: UUID,
    calc_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NonTaxableCalculationResponse:
    try:
        return nontaxable_calculation_service.get_calculation(
            db, case_id, calc_id, current_user
        )
    except (CaseNotFound, NonTaxableCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete(
    "/cases/{case_id}/nontaxable-calculations/{calc_id}",
    status_code=204,
)
def delete_nontaxable_calculation(
    case_id: UUID,
    calc_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        nontaxable_calculation_service.delete_calculation(
            db, case_id, calc_id, current_user
        )
    except (CaseNotFound, NonTaxableCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)
