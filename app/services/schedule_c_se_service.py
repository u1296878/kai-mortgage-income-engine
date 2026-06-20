import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.models.self_employment_calculation import SelfEmploymentCalculation
from app.repositories import self_employment_calculation_repo
from app.schemas.extraction import ExtractedField
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear
from app.schemas.self_employment_results import SelfEmploymentCalculationRequest
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
    calculations = []
    for index in _business_indexes(by_name):
        source_key = f"business_{index}"
        if self_employment_calculation_repo.get_by_source(db, document_id, source_key):
            continue
        request = _build_request(by_name, index)
        if request is None:
            continue
        result = run_self_employment_engine(request)
        calculation = SelfEmploymentCalculation(
            case_id=str(case_id),
            label=f"Schedule C business {index}",
            kind=result.kind,
            inputs=request.model_dump(mode="json"),
            qualifying_monthly=result.qualifying_monthly,
            annual_income=result.annual_income,
            breakdown=result.breakdown,
            included=True,
            source_document_id=str(document_id),
            source_business_key=source_key,
        )
        saved = self_employment_calculation_repo.create(db, calculation)
        log_event(
            "schedule_c_self_employment_draft_created",
            {"calculation_id": saved.id, "document_id": str(document_id), "source_key": source_key},
        )
        calculations.append(saved)
    return calculations


def _build_request(
    by_name: dict[str, ExtractedField],
    index: int,
) -> SelfEmploymentCalculationRequest | None:
    prefix = f"schedule_c_business_{index}"
    if _schedule_c_value(by_name, index, "net_profit") is None:
        return None
    year = ScheduleCYear(
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
