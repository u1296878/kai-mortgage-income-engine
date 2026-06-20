import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.models.self_employment_calculation import SelfEmploymentCalculation
from app.repositories import self_employment_calculation_repo
from app.schemas.extraction import ExtractedField
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear
from app.schemas.self_employment_results import SelfEmploymentCalculationRequest
from app.services import schedule_c_draft_merge
from app.services.schedule_c_business_match import build_identity
from app.services.self_employment_income_service import run_self_employment_engine

MODEL_FIELD_ALIASES = {
    "net_profit": "schedule_c_net_profit",
    "nonrecurring_income": "schedule_c_nonrecurring_income",
    "depletion": "schedule_c_depletion",
    "depreciation": "schedule_c_depreciation",
    "meals_entertainment_exclusion": "schedule_c_meals_exclusion",
    "business_use_of_home": "schedule_c_business_use_of_home",
    "business_miles": "schedule_c_business_miles",
    "amortization_casualty": "schedule_c_amortization_casualty",
}


def create_drafts_from_fields(
    db: Session,
    case_id: UUID,
    document_id: UUID,
    fields: list[ExtractedField],
) -> list[SelfEmploymentCalculation]:
    by_name = {field.field: field for field in fields}
    indexes = _business_indexes(by_name)
    existing = self_employment_calculation_repo.list_by_case(db, case_id)
    calculations = []
    for index in indexes:
        identity = build_identity(by_name, index, len(indexes))
        year = _build_year(by_name, index)
        if year is None:
            continue
        matched = schedule_c_draft_merge.matching_calculation(existing, identity)
        if matched is not None:
            saved = schedule_c_draft_merge.merge_year(db, matched, identity, year)
            if saved is not None:
                calculations.append(saved)
            continue
        request = _build_request(year)
        result = run_self_employment_engine(request)
        calculation = SelfEmploymentCalculation(
            case_id=str(case_id),
            label=identity.label,
            kind=result.kind,
            inputs=request.model_dump(mode="json"),
            qualifying_monthly=result.qualifying_monthly,
            annual_income=result.annual_income,
            breakdown=schedule_c_draft_merge.with_review_flags(
                result.breakdown,
                identity.review_flags,
            ),
            included=True,
            source_document_id=str(document_id),
            source_business_key=identity.source_key,
        )
        saved = self_employment_calculation_repo.create(db, calculation)
        existing.append(saved)
        log_event(
            "schedule_c_self_employment_draft_created",
            {
                "calculation_id": saved.id,
                "document_id": str(document_id),
                "source_key": identity.source_key,
            },
        )
        calculations.append(saved)
    return calculations


def _build_year(
    by_name: dict[str, ExtractedField],
    index: int,
) -> ScheduleCYear | None:
    if _schedule_c_value(by_name, index, "net_profit") is None:
        return None
    return ScheduleCYear(
        months=12.0,
        tax_year=_tax_year(by_name),
        net_profit=_schedule_c_value(by_name, index, "net_profit"),
        nonrecurring_income=_schedule_c_value(by_name, index, "nonrecurring_income") or 0.0,
        depletion=_schedule_c_value(by_name, index, "depletion") or 0.0,
        depreciation=_schedule_c_value(by_name, index, "depreciation") or 0.0,
        meals_entertainment_exclusion=_schedule_c_value(by_name, index, "meals_entertainment_exclusion") or 0.0,
        business_use_of_home=_schedule_c_value(by_name, index, "business_use_of_home") or 0.0,
        business_miles=_schedule_c_value(by_name, index, "business_miles") or 0.0,
        amortization_casualty=_schedule_c_value(by_name, index, "amortization_casualty") or 0.0,
    )


def _build_request(year: ScheduleCYear) -> SelfEmploymentCalculationRequest:
    return SelfEmploymentCalculationRequest(
        kind="schedule_c",
        payload=ScheduleCInput(years=[year]).model_dump(mode="json"),
    )


def _business_indexes(by_name: dict[str, ExtractedField]) -> list[int]:
    indexes = set()
    for field_name in by_name:
        match = re.fullmatch(r"schedule_c_business_(\d+)_net_profit", field_name)
        if match:
            indexes.add(int(match.group(1)))
    if "schedule_c_net_profit" in by_name:
        indexes.add(1)
    return sorted(indexes)


def _tax_year(by_name: dict[str, ExtractedField]) -> int | None:
    value = _value(by_name, "tax_year")
    return int(value) if value is not None else None


def _value(by_name: dict[str, ExtractedField], field_name: str) -> float | None:
    field = by_name.get(field_name)
    return field.value if field else None


def _schedule_c_value(
    by_name: dict[str, ExtractedField],
    index: int,
    suffix: str,
) -> float | None:
    indexed = _value(by_name, f"schedule_c_business_{index}_{suffix}")
    if indexed is not None or index != 1:
        return indexed
    return _value(by_name, MODEL_FIELD_ALIASES[suffix])
