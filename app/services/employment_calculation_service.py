"""Persist computed employment worksheets to a case."""

from dataclasses import asdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import EmploymentCalculationNotFound
from app.income.employment import compute_employment_income
from app.models.employment_calculation import EmploymentCalculation
from app.repositories import case_repo, employment_calculation_repo
from app.schemas.income_inputs import EmploymentInput


def create_calculation(
    db: Session,
    case_id: UUID,
    employment_input: EmploymentInput,
    borrower_id: UUID | None,
    label: str | None,
) -> EmploymentCalculation:
    case = case_repo.get_case(db, case_id)
    result = compute_employment_income(employment_input)
    calculation = EmploymentCalculation(
        case_id=case.id,
        borrower_id=str(borrower_id) if borrower_id else None,
        label=label,
        inputs=employment_input.model_dump(mode="json"),
        total_monthly=result.total_monthly,
        annual_income=round(result.total_monthly * 12, 2),
        breakdown=asdict(result),
    )
    saved = employment_calculation_repo.create(db, calculation)
    log_event(
        "employment_calculation_created",
        {
            "calculation_id": saved.id,
            "case_id": saved.case_id,
            "total_monthly": saved.total_monthly,
            "annual_income": saved.annual_income,
        },
    )
    return saved


def list_calculations_by_case(
    db: Session,
    case_id: UUID,
) -> list[EmploymentCalculation]:
    case_repo.get_case(db, case_id)
    return employment_calculation_repo.list_by_case(db, case_id)


def get_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
) -> EmploymentCalculation:
    case_repo.get_case(db, case_id)
    calculation = employment_calculation_repo.get(db, calc_id)
    if calculation.case_id != str(case_id):
        raise EmploymentCalculationNotFound(f"Employment calculation not found: {calc_id}")
    return calculation


def delete_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
) -> None:
    get_calculation(db, case_id, calc_id)
    employment_calculation_repo.delete(db, calc_id)
    log_event(
        "employment_calculation_deleted",
        {"calculation_id": str(calc_id), "case_id": str(case_id)},
    )
