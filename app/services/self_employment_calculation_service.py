"""Persist self-employment worksheets to a case."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import SelfEmploymentCalculationNotFound
from app.models.self_employment_calculation import SelfEmploymentCalculation
from app.repositories import case_repo, self_employment_calculation_repo
from app.schemas.self_employment_results import (
    SelfEmploymentCalculationCreate,
    SelfEmploymentCalculationRequest,
    SelfEmploymentCalculationUpdate,
)
from app.services.self_employment_income_service import run_self_employment_engine


def create_calculation(
    db: Session,
    case_id: UUID,
    payload: SelfEmploymentCalculationCreate,
) -> SelfEmploymentCalculation:
    case = case_repo.get_case(db, case_id)
    request = _to_calculation_request(payload)
    result = run_self_employment_engine(request)
    calculation = SelfEmploymentCalculation(
        case_id=case.id,
        borrower_id=str(payload.borrower_id) if payload.borrower_id else None,
        label=payload.label,
        kind=result.kind,
        inputs=request.model_dump(mode="json"),
        qualifying_monthly=result.qualifying_monthly,
        annual_income=result.annual_income,
        included=payload.included,
        breakdown=result.breakdown,
    )
    saved = self_employment_calculation_repo.create(db, calculation)
    log_event(
        "self_employment_calculation_created",
        {"calculation_id": saved.id, "case_id": saved.case_id},
    )
    return saved


def list_calculations_by_case(
    db: Session,
    case_id: UUID,
) -> list[SelfEmploymentCalculation]:
    case_repo.get_case(db, case_id)
    return self_employment_calculation_repo.list_by_case(db, case_id)


def get_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
) -> SelfEmploymentCalculation:
    case_repo.get_case(db, case_id)
    calculation = self_employment_calculation_repo.get(db, calc_id)
    if calculation.case_id != str(case_id):
        raise SelfEmploymentCalculationNotFound(
            f"Self-employment calculation not found: {calc_id}",
        )
    return calculation


def delete_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
) -> None:
    get_calculation(db, case_id, calc_id)
    self_employment_calculation_repo.delete(db, calc_id)
    log_event(
        "self_employment_calculation_deleted",
        {"calculation_id": str(calc_id), "case_id": str(case_id)},
    )


def update_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
    payload: SelfEmploymentCalculationUpdate,
) -> SelfEmploymentCalculation:
    calculation = get_calculation(db, case_id, calc_id)
    calculation.included = payload.included
    saved = self_employment_calculation_repo.update(db, calculation)
    log_event(
        "self_employment_calculation_updated",
        {"calculation_id": saved.id, "case_id": saved.case_id},
    )
    return saved


def _to_calculation_request(
    payload: SelfEmploymentCalculationCreate,
) -> SelfEmploymentCalculationRequest:
    return SelfEmploymentCalculationRequest.model_validate(
        payload.model_dump(exclude={"borrower_id", "label", "included"}),
    )
