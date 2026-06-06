from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import (
    CaseNotFound,
    InvalidRentalInput,
    RentalCalculationNotFound,
)
from app.models.user import User
from app.schemas.rental_inputs import RentalCalculationCreate, RentalProperty
from app.schemas.rental_results import RentalCalculationResponse
from app.services import rental_calculation_service

router = APIRouter(tags=["rental_calculations"])


@router.post(
    "/cases/{case_id}/rental-calculations",
    response_model=RentalCalculationResponse,
)
def create_rental_calculation(
    case_id: UUID,
    payload: RentalCalculationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RentalCalculationResponse:
    property_input = RentalProperty.model_validate(
        payload.model_dump(exclude={"borrower_id", "label"}),
    )
    try:
        return rental_calculation_service.create_calculation(
            db,
            case_id,
            property_input,
            payload.borrower_id,
            payload.label,
            current_user,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRentalInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "/cases/{case_id}/rental-calculations",
    response_model=list[RentalCalculationResponse],
)
def list_rental_calculations(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[RentalCalculationResponse]:
    try:
        return rental_calculation_service.list_calculations_by_case(
            db,
            case_id,
            current_user,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get(
    "/cases/{case_id}/rental-calculations/{calc_id}",
    response_model=RentalCalculationResponse,
)
def get_rental_calculation(
    case_id: UUID,
    calc_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RentalCalculationResponse:
    try:
        return rental_calculation_service.get_calculation(
            db,
            case_id,
            calc_id,
            current_user,
        )
    except (CaseNotFound, RentalCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete(
    "/cases/{case_id}/rental-calculations/{calc_id}",
    status_code=204,
)
def delete_rental_calculation(
    case_id: UUID,
    calc_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        rental_calculation_service.delete_calculation(
            db,
            case_id,
            calc_id,
            current_user,
        )
    except (CaseNotFound, RentalCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)
