import re
from dataclasses import asdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.income.dates import months_between
from app.income.employment import compute_employment_income
from app.models.employment_calculation import EmploymentCalculation
from app.repositories import employment_calculation_repo
from app.schemas.income_inputs import BasePay, EmploymentInput, EmploymentPeriod, VariableBucket
from app.services.schedule_c_draft_merge import with_review_flags

YEAR_CONFLICT_FLAG = "Employment draft already has income for this tax year; verify the uploaded source."


def upsert_period(
    db: Session,
    case_id: UUID,
    document_id: UUID,
    employer: str | None,
    period: EmploymentPeriod,
    review_flags: list[str],
    options: dict[str, str],
) -> list[EmploymentCalculation]:
    if _already_processed(db, case_id, document_id):
        return []
    source_key = source_key_for(employer, document_id)
    existing = employment_calculation_repo.list_by_case(db, case_id)
    flags = [*review_flags, *_identity_flags(employer, options["missing_employer_flag"])]
    matched = _matching_calculation(existing, source_key)
    if matched is not None:
        saved = _merge_period(db, matched, period, flags, options["updated_event"])
        return [saved] if saved is not None else []
    saved = _create_calculation(db, case_id, document_id, employer, source_key, period, flags, options)
    return [saved]


def source_key_for(employer: str | None, document_id: UUID) -> str:
    if not employer:
        return f"document:{document_id}"
    return f"employer:{_normalize(employer)}"


def employment_input(periods: list[EmploymentPeriod]) -> EmploymentInput:
    empty = VariableBucket(periods=[], use_ytd=True)
    return EmploymentInput(
        # Uploaded employment documents give combined wages; paystubs can split buckets later.
        base_pay=BasePay(periods=periods),
        overtime=empty,
        bonus=empty,
        commission=empty,
        other=empty,
    )


def annual_income(periods: list[EmploymentPeriod]) -> float:
    total_months = sum(months_between(period.date_from, period.date_through) for period in periods)
    if total_months == 0:
        return 0.0
    return round(sum(period.total_earnings for period in periods) / total_months * 12, 2)


def _create_calculation(
    db: Session,
    case_id: UUID,
    document_id: UUID,
    employer: str | None,
    source_key: str,
    period: EmploymentPeriod,
    review_flags: list[str],
    options: dict[str, str],
) -> EmploymentCalculation:
    source = employment_input([period])
    result = compute_employment_income(source)
    calculation = EmploymentCalculation(
        case_id=str(case_id),
        label=_label(options["label_prefix"], employer),
        inputs=source.model_dump(mode="json"),
        total_monthly=result.total_monthly,
        annual_income=annual_income([period]),
        breakdown=with_review_flags(asdict(result), review_flags),
        included=True,
        source_document_id=str(document_id),
        source_employer_key=source_key,
    )
    saved = employment_calculation_repo.create(db, calculation)
    log_event(options["created_event"], {"calculation_id": saved.id, "document_id": str(document_id), "source_key": source_key})
    return saved


def _merge_period(
    db: Session,
    calculation: EmploymentCalculation,
    period: EmploymentPeriod,
    review_flags: list[str],
    event_name: str,
) -> EmploymentCalculation | None:
    source = EmploymentInput.model_validate(calculation.inputs)
    if (existing := _same_year_period(source, period)) is not None:
        if abs(existing.total_earnings - period.total_earnings) <= 1:
            return None
        calculation.breakdown = with_review_flags(calculation.breakdown, [*review_flags, YEAR_CONFLICT_FLAG])
        return employment_calculation_repo.update(db, calculation)
    periods = sorted([*source.base_pay.periods, period], key=lambda item: item.date_from, reverse=True)
    result = compute_employment_income(employment_input(periods))
    calculation.inputs = employment_input(periods).model_dump(mode="json")
    calculation.total_monthly = result.total_monthly
    calculation.annual_income = annual_income(periods)
    calculation.breakdown = with_review_flags(asdict(result), review_flags)
    saved = employment_calculation_repo.update(db, calculation)
    log_event(event_name, {"calculation_id": saved.id, "source_key": saved.source_employer_key})
    return saved


def _matching_calculation(existing: list[EmploymentCalculation], source_key: str) -> EmploymentCalculation | None:
    if source_key.startswith("document:"):
        return None
    return next((calc for calc in existing if calc.source_employer_key == source_key), None)


def _already_processed(db: Session, case_id: UUID, document_id: UUID) -> bool:
    return any(calc.source_document_id == str(document_id) for calc in employment_calculation_repo.list_by_case(db, case_id))


def _same_year_period(source: EmploymentInput, period: EmploymentPeriod) -> EmploymentPeriod | None:
    return next((item for item in source.base_pay.periods if item.date_from.year == period.date_from.year), None)


def _label(prefix: str, employer: str | None) -> str:
    return f"{prefix} - {employer}" if employer else f"{prefix} employment"


def _identity_flags(employer: str | None, missing_flag: str) -> list[str]:
    return [] if employer else [missing_flag]


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))
