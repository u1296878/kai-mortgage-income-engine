from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.exceptions import (
    InvalidEmploymentInput,
    InvalidNonTaxableInput,
    InvalidRentalInput,
)
from app.models.user import User
from app.schemas.income_inputs import EmploymentInput
from app.schemas.income_results import EmploymentResult
from app.schemas.nontaxable_inputs import NonTaxableCalculationRequest
from app.schemas.nontaxable_results import NonTaxableResult
from app.schemas.rental_inputs import RentalProperty
from app.schemas.rental_results import RentalResult
from app.services import (
    employment_income_service,
    nontaxable_income_service,
    rental_income_service,
)

router = APIRouter(prefix="/income", tags=["income"])


@router.post("/employment/calculate", response_model=EmploymentResult)
def calculate_employment_income(
    employment: EmploymentInput,
    current_user: Annotated[User, Depends(get_current_user)],
) -> EmploymentResult:
    try:
        return employment_income_service.calculate_employment_income(employment)
    except InvalidEmploymentInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/rental/calculate", response_model=RentalResult)
def calculate_rental_income(
    property_input: RentalProperty,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RentalResult:
    try:
        return rental_income_service.calculate_rental_income(property_input)
    except InvalidRentalInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/nontaxable/calculate", response_model=NonTaxableResult)
def calculate_nontaxable_income(
    request: NonTaxableCalculationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> NonTaxableResult:
    try:
        return nontaxable_income_service.calculate_nontaxable_income(request)
    except InvalidNonTaxableInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
