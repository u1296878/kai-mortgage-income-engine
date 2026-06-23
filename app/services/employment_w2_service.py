import re
from dataclasses import asdict
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.income.employment import compute_employment_income
from app.models.employment_calculation import EmploymentCalculation
from app.repositories import employment_calculation_repo
from app.schemas.extraction import ExtractedField
from app.schemas.income_inputs import BasePay, EmploymentInput, EmploymentPeriod, VariableBucket
from app.services.schedule_c_draft_merge import with_review_flags

MISSING_EMPLOYER_FLAG = "W-2 employer name is missing; verify before merging with other W-2 income."


def create_drafts_from_fields(
    db: Session,
    case_id: UUID,
    document_id: UUID,
    fields: list[ExtractedField],
    review_flags: list[str] | None = None,
) -> list[EmploymentCalculation]:
    by_name = {field.field: field for field in fields}
    wages = _value(by_name, "w2_wages")
    tax_year = _tax_year(by_name)
    if wages is None or tax_year is None or _already_processed(db, case_id, document_id):
        return []
    employer = _text(by_name, "w2_employer_name")
    source_key = _source_key(employer, document_id)
    period = _period(tax_year, wages)
    existing = employment_calculation_repo.list_by_case(db, case_id)
    matched = _matching_calculation(existing, source_key)
    flags = [*(review_flags or []), *_identity_flags(employer)]
    if matched is not None:
        saved = _merge_period(db, matched, period, flags)
        return [saved] if saved is not None else []
    saved = _create_calculation(db, case_id, document_id, employer, source_key, period, flags)
    return [saved]


def _create_calculation(
    db: Session, case_id: UUID, document_id: UUID, employer: str | None,
    source_key: str, period: EmploymentPeriod, review_flags: list[str],
) -> EmploymentCalculation:
    employment_input = _employment_input([period])
    result = compute_employment_income(employment_input)
    calculation = EmploymentCalculation(
        case_id=str(case_id),
        label=_label(employer),
        inputs=employment_input.model_dump(mode="json"),
        total_monthly=result.total_monthly,
        annual_income=_annual_income([period]),
        breakdown=with_review_flags(asdict(result), review_flags),
        included=True,
        source_document_id=str(document_id),
        source_employer_key=source_key,
    )
    saved = employment_calculation_repo.create(db, calculation)
    log_event(
        "w2_employment_draft_created",
        {"calculation_id": saved.id, "document_id": str(document_id), "source_key": source_key},
    )
    return saved


def _merge_period(
    db: Session, calculation: EmploymentCalculation, period: EmploymentPeriod,
    review_flags: list[str],
) -> EmploymentCalculation | None:
    source = EmploymentInput.model_validate(calculation.inputs)
    if _has_year(source, period.date_from.year) or len(source.base_pay.periods) >= 2:
        return None
    periods = sorted([*source.base_pay.periods, period], key=lambda item: item.date_from, reverse=True)
    employment_input = _employment_input(periods)
    result = compute_employment_income(employment_input)
    calculation.inputs = employment_input.model_dump(mode="json")
    calculation.total_monthly = result.total_monthly
    calculation.annual_income = _annual_income(periods)
    calculation.breakdown = with_review_flags(asdict(result), review_flags)
    saved = employment_calculation_repo.update(db, calculation)
    log_event(
        "w2_employment_draft_updated",
        {"calculation_id": saved.id, "source_key": saved.source_employer_key},
    )
    return saved


def _employment_input(periods: list[EmploymentPeriod]) -> EmploymentInput:
    empty = VariableBucket(periods=[], use_ytd=True)
    return EmploymentInput(
        # W-2 Box 1 combines base, OT, bonus, and other wages; paystubs can split later.
        base_pay=BasePay(periods=periods),
        overtime=empty,
        bonus=empty,
        commission=empty,
        other=empty,
    )


def _period(tax_year: int, wages: float) -> EmploymentPeriod:
    return EmploymentPeriod(
        date_from=date(tax_year, 1, 1),
        date_through=date(tax_year, 12, 31),
        total_earnings=wages,
        included=True,
    )


def _matching_calculation(
    existing: list[EmploymentCalculation],
    source_key: str,
) -> EmploymentCalculation | None:
    if source_key.startswith("document:"):
        return None
    return next((calc for calc in existing if calc.source_employer_key == source_key), None)


def _already_processed(db: Session, case_id: UUID, document_id: UUID) -> bool:
    return any(calc.source_document_id == str(document_id) for calc in employment_calculation_repo.list_by_case(db, case_id))


def _has_year(source: EmploymentInput, tax_year: int) -> bool:
    return any(period.date_from.year == tax_year for period in source.base_pay.periods)


def _annual_income(periods: list[EmploymentPeriod]) -> float:
    return round(sum(period.total_earnings for period in periods) / len(periods), 2)


def _tax_year(by_name: dict[str, ExtractedField]) -> int | None:
    value = _value(by_name, "tax_year")
    if value is None:
        value = _value(by_name, "w2_tax_year")
    return int(value) if value is not None else None


def _value(by_name: dict[str, ExtractedField], field_name: str) -> float | None:
    field = by_name.get(field_name)
    return field.value if field else None


def _text(by_name: dict[str, ExtractedField], field_name: str) -> str | None:
    field = by_name.get(field_name)
    if field is None:
        return None
    text = field.raw_text or str(field.value or "")
    return text.strip() or None


def _source_key(employer: str | None, document_id: UUID) -> str:
    if not employer:
        return f"document:{document_id}"
    return f"employer:{_normalize(employer)}"


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _label(employer: str | None) -> str:
    return f"W-2 - {employer}" if employer else "W-2 employment"


def _identity_flags(employer: str | None) -> list[str]:
    return [] if employer else [MISSING_EMPLOYER_FLAG]
