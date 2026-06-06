"""Stateless service: run the employment engine and map to the API contract."""

from dataclasses import asdict

from app.audit.logger import log_event
from app.income.employment import compute_employment_income
from app.schemas.income_inputs import EmploymentInput
from app.schemas.income_results import EmploymentResult


def calculate_employment_income(employment: EmploymentInput) -> EmploymentResult:
    result = compute_employment_income(employment)
    log_event("employment_income_calculated", {"total_monthly": result.total_monthly})
    return EmploymentResult.model_validate(asdict(result))
