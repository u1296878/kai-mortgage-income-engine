"""Persist self-employment worksheets to a case (broker/manager scoped)."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import CaseNotFound, SelfEmploymentCalculationNotFound
from app.models.case import Case
from app.models.self_employment_calculation import SelfEmploymentCalculation
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import case_repo, self_employment_calculation_repo
from app.schemas.self_employment_results import (
    SelfEmploymentCalculationCreate,
    SelfEmploymentCalculationRequest,
)
from app.services.self_employment_income_service import run_self_employment_engine


def create_calculation(
    db: Session,
    case_id: UUID,
    payload: SelfEmploymentCalculationCreate,
    current_user: User,
) -> SelfEmploymentCalculation:
    case = _get_accessible_case(db, case_id, current_user)
    request = _to_calculation_request(payload)
    result = run_self_employment_engine(request)
    calculation = SelfEmploymentCalculation(
        case_id=case.id,
        broker_id=case.broker_id,
        borrower_id=str(payload.borrower_id) if payload.borrower_id else None,
        label=payload.label,
        kind=result.kind,
        inputs=request.model_dump(mode="json"),
        qualifying_monthly=result.qualifying_monthly,
        annual_income=result.annual_income,
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
    current_user: User,
) -> list[SelfEmploymentCalculation]:
    _get_accessible_case(db, case_id, current_user)
    return self_employment_calculation_repo.list_by_case(db, case_id)


def get_calculation(
    db: Session,
    case_id: UUID,
    calc_id: UUID,
    current_user: User,
) -> SelfEmploymentCalculation:
    _get_accessible_case(db, case_id, current_user)
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
    current_user: User,
) -> None:
    get_calculation(db, case_id, calc_id, current_user)
    self_employment_calculation_repo.delete(db, calc_id)
    log_event(
        "self_employment_calculation_deleted",
        {"calculation_id": str(calc_id), "case_id": str(case_id)},
    )


def _to_calculation_request(
    payload: SelfEmploymentCalculationCreate,
) -> SelfEmploymentCalculationRequest:
    return SelfEmploymentCalculationRequest.model_validate(
        payload.model_dump(exclude={"borrower_id", "label"}),
    )


def _get_accessible_case(db: Session, case_id: UUID, current_user: User) -> Case:
    case = case_repo.get_case(db, case_id)
    if not _is_manager(current_user) and case.broker_id != current_user.id:
        raise CaseNotFound(f"Case not found: {case_id}")
    return case


def _is_manager(user: User) -> bool:
    return user.role == UserRole.manager.value
