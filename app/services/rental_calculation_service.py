"""Persist computed rental worksheets to a case."""

from dataclasses import asdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import CaseNotFound, RentalCalculationNotFound
from app.income.rental import compute_rental_income
from app.models.case import Case
from app.models.rental_calculation import RentalCalculation
from app.repositories import case_repo, rental_calculation_repo
from app.schemas.rental_inputs import RentalProperty


def create_calculation(
    db: Session,
    case_id: UUID,
    property_input: RentalProperty,
    borrower_id: UUID | None,
    label: str | None,
    local_user_id: UUID,
    included: bool = True,
) -> RentalCalculation:
    case = _get_accessible_case(db, case_id, local_user_id)
    result = compute_rental_income(property_input)
    calculation = RentalCalculation(
        case_id=case.id,
        broker_id=case.broker_id,
        borrower_id=str(borrower_id) if borrower_id else None,
        label=label,
        inputs=property_input.model_dump(mode="json"),
        qualifying_monthly=result.qualifying_monthly,
        # annual_income may be negative for a rental loss; never clamped.
        annual_income=round(result.qualifying_monthly * 12, 2),
        included=included,
        breakdown=asdict(result),
    )
    saved = rental_calculation_repo.create(db, calculation)
    log_event(
        "rental_calculation_created",
        {
            "calculation_id": saved.id,
            "case_id": saved.case_id,
            "qualifying_monthly": saved.qualifying_monthly,
            "annual_income": saved.annual_income,
        },
    )
    return saved


def update_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
    property_input: RentalProperty,
    borrower_id: UUID | None,
    label: str | None,
    included: bool | None,
    local_user_id: UUID,
) -> RentalCalculation:
    calculation = get_calculation(db, case_id, calc_id, local_user_id)
    result = compute_rental_income(property_input)
    updated = rental_calculation_repo.update(
        db,
        UUID(calculation.id),
        {
            "borrower_id": str(borrower_id) if borrower_id else None,
            "label": label,
            "inputs": property_input.model_dump(mode="json"),
            "qualifying_monthly": result.qualifying_monthly,
            "annual_income": round(result.qualifying_monthly * 12, 2),
            "included": calculation.included if included is None else included,
            "breakdown": asdict(result),
        },
    )
    log_event("rental_calculation_updated", {"calculation_id": updated.id})
    return updated


def update_calculation_included(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
    included: bool,
    local_user_id: UUID,
) -> RentalCalculation:
    get_calculation(db, case_id, calc_id, local_user_id)
    updated = rental_calculation_repo.update(db, calc_id, {"included": included})
    log_event("rental_calculation_inclusion_updated", {"calculation_id": updated.id})
    return updated


def list_calculations_by_case(
    db: Session,
    case_id: UUID,
    local_user_id: UUID,
) -> list[RentalCalculation]:
    _get_accessible_case(db, case_id, local_user_id)
    return rental_calculation_repo.list_by_case(db, case_id)


def get_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
    local_user_id: UUID,
) -> RentalCalculation:
    _get_accessible_case(db, case_id, local_user_id)
    calculation = rental_calculation_repo.get(db, calc_id)
    if calculation.case_id != str(case_id):
        raise RentalCalculationNotFound(f"Rental calculation not found: {calc_id}")
    return calculation


def delete_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
    local_user_id: UUID,
) -> None:
    get_calculation(db, case_id, calc_id, local_user_id)
    rental_calculation_repo.delete(db, calc_id)
    log_event(
        "rental_calculation_deleted",
        {"calculation_id": str(calc_id), "case_id": str(case_id)},
    )


def _get_accessible_case(db: Session, case_id: UUID, local_user_id: UUID) -> Case:
    case = case_repo.get_case(db, case_id)
    # TODO step 2b: remove ownership plumbing.
    if case.broker_id != str(local_user_id):
        raise CaseNotFound(f"Case not found: {case_id}")
    return case
