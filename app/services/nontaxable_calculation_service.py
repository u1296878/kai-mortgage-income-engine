"""Persist non-taxable/SS worksheets to a case (broker/manager scoped)."""

from dataclasses import asdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import CaseNotFound, NonTaxableCalculationNotFound
from app.models.case import Case
from app.models.nontaxable_calculation import NonTaxableCalculation
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import case_repo, nontaxable_calculation_repo
from app.schemas.nontaxable_inputs import (
    NonTaxableCalculationCreate,
    NonTaxableCalculationRequest,
)
from app.services.nontaxable_income_service import run_nontaxable_engine


def create_calculation(
    db: Session,
    case_id: UUID,
    payload: NonTaxableCalculationCreate,
    current_user: User,
) -> NonTaxableCalculation:
    case = _get_accessible_case(db, case_id, current_user)
    request = _to_calculation_request(payload)
    result = run_nontaxable_engine(request)
    calculation = NonTaxableCalculation(
        case_id=case.id,
        broker_id=case.broker_id,
        borrower_id=str(payload.borrower_id) if payload.borrower_id else None,
        label=payload.label,
        kind=payload.kind.value,
        inputs=request.model_dump(mode="json"),
        monthly=result.monthly,
        annual_income=round(result.monthly * 12, 2),
        breakdown=asdict(result),
    )
    saved = nontaxable_calculation_repo.create(db, calculation)
    log_event(
        "nontaxable_calculation_created",
        {"calculation_id": saved.id, "case_id": saved.case_id},
    )
    return saved


def list_calculations_by_case(
    db: Session,
    case_id: UUID,
    current_user: User,
) -> list[NonTaxableCalculation]:
    _get_accessible_case(db, case_id, current_user)
    return nontaxable_calculation_repo.list_by_case(db, case_id)


def get_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
    current_user: User,
) -> NonTaxableCalculation:
    _get_accessible_case(db, case_id, current_user)
    calculation = nontaxable_calculation_repo.get(db, calc_id)
    if calculation.case_id != str(case_id):
        raise NonTaxableCalculationNotFound(
            f"Non-taxable calculation not found: {calc_id}",
        )
    return calculation


def delete_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
    current_user: User,
) -> None:
    get_calculation(db, case_id, calc_id, current_user)
    nontaxable_calculation_repo.delete(db, calc_id)
    log_event(
        "nontaxable_calculation_deleted",
        {"calculation_id": str(calc_id), "case_id": str(case_id)},
    )


def _to_calculation_request(
    payload: NonTaxableCalculationCreate,
) -> NonTaxableCalculationRequest:
    return NonTaxableCalculationRequest.model_validate(
        payload.model_dump(exclude={"borrower_id", "label"}),
    )


def _get_accessible_case(db: Session, case_id: UUID, current_user: User) -> Case:
    case = case_repo.get_case(db, case_id)
    if not _is_manager(current_user) and case.broker_id != current_user.id:
        raise CaseNotFound(f"Case not found: {case_id}")
    return case


def _is_manager(user: User) -> bool:
    return user.role == UserRole.manager.value
