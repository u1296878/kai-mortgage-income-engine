"""Stateless service: run the rental engine and map to the API contract."""

from dataclasses import asdict

from app.audit.logger import log_event
from app.income.rental import compute_rental_income
from app.schemas.rental_inputs import RentalProperty
from app.schemas.rental_results import RentalResult


def calculate_rental_income(property_input: RentalProperty) -> RentalResult:
    result = compute_rental_income(property_input)
    log_event("rental_income_calculated", {"qualifying_monthly": result.qualifying_monthly})
    return RentalResult.model_validate(asdict(result))
