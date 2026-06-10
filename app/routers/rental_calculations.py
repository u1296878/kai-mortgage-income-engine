from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.exceptions import (
    CaseNotFound,
    InvalidRentalInput,
    RentalCalculationNotFound,
)
from app.runtime.local_user import LOCAL_USER_ID
from app.schemas.rental_inputs import (
    RentalCalculationCreate,
    RentalCalculationUpdate,
    RentalProperty,
)
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
            LOCAL_USER_ID,
            payload.included,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRentalInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch(
    "/cases/{case_id}/rental-calculations/{calc_id}",
    response_model=RentalCalculationResponse,
)
def update_rental_calculation(
    case_id: UUID,
    calc_id: UUID,
    payload: RentalCalculationUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> RentalCalculationResponse:
    try:
        if not _has_property_update(payload):
            if payload.included is None:
                raise HTTPException(status_code=422, detail="No rental calculation updates provided")
            return rental_calculation_service.update_calculation_included(
                db, case_id, calc_id, payload.included, LOCAL_USER_ID
            )
        property_input = RentalProperty.model_validate(
            payload.model_dump(
                exclude={"borrower_id", "label", "included"},
                exclude_none=True,
            ),
        )
        return rental_calculation_service.update_calculation(
            db,
            case_id,
            calc_id,
            property_input,
            payload.borrower_id,
            payload.label,
            payload.included,
            LOCAL_USER_ID,
        )
    except (CaseNotFound, RentalCalculationNotFound) as error:
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
) -> list[RentalCalculationResponse]:
    try:
        return rental_calculation_service.list_calculations_by_case(
            db,
            case_id,
            LOCAL_USER_ID,
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
) -> RentalCalculationResponse:
    try:
        return rental_calculation_service.get_calculation(
            db,
            case_id,
            calc_id,
            LOCAL_USER_ID,
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
) -> Response:
    try:
        rental_calculation_service.delete_calculation(
            db,
            case_id,
            calc_id,
            LOCAL_USER_ID,
        )
    except (CaseNotFound, RentalCalculationNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)


def _has_property_update(payload: RentalCalculationUpdate) -> bool:
    property_fields = {
        "property_class",
        "method",
        "schedule_e_years",
        "monthly_pitia",
        "gross_monthly_rent",
        "vacancy_factor",
    }
    updates = payload.model_dump(exclude_none=True)
    return any(field in updates for field in property_fields)
