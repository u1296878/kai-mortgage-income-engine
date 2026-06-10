from fastapi import APIRouter, HTTPException

from app.exceptions import (
    InvalidEmploymentInput,
    InvalidNonTaxableInput,
    InvalidRentalInput,
    InvalidSelfEmploymentInput,
)
from app.schemas.income_inputs import EmploymentInput
from app.schemas.income_results import EmploymentResult
from app.schemas.nontaxable_inputs import NonTaxableCalculationRequest
from app.schemas.nontaxable_results import NonTaxableResult
from app.schemas.rental_inputs import RentalProperty
from app.schemas.rental_results import RentalResult
from app.schemas.self_employment_results import (
    SelfEmploymentCalculationRequest,
    SelfEmploymentResult,
)
from app.services import (
    employment_income_service,
    nontaxable_income_service,
    rental_income_service,
    self_employment_income_service,
)

router = APIRouter(prefix="/income", tags=["income"])


@router.post("/employment/calculate", response_model=EmploymentResult)
def calculate_employment_income(
    employment: EmploymentInput,
) -> EmploymentResult:
    try:
        return employment_income_service.calculate_employment_income(employment)
    except InvalidEmploymentInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/rental/calculate", response_model=RentalResult)
def calculate_rental_income(
    property_input: RentalProperty,
) -> RentalResult:
    try:
        return rental_income_service.calculate_rental_income(property_input)
    except InvalidRentalInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/nontaxable/calculate", response_model=NonTaxableResult)
def calculate_nontaxable_income(
    request: NonTaxableCalculationRequest,
) -> NonTaxableResult:
    try:
        return nontaxable_income_service.calculate_nontaxable_income(request)
    except InvalidNonTaxableInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/self-employment/calculate", response_model=SelfEmploymentResult)
def calculate_self_employment_income(
    request: SelfEmploymentCalculationRequest,
) -> SelfEmploymentResult:
    try:
        return self_employment_income_service.calculate_self_employment_income(request)
    except InvalidSelfEmploymentInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
