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


def create_drafts_from_fields(
    db: Session,
    case_id: UUID,
    broker_id: UUID,
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
            broker_id=str(broker_id),
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
    if f"{prefix}_net_profit" not in by_name:
        return None
    year = ScheduleCYear(
        months=12.0,
        tax_year=_tax_year(by_name),
        net_profit=_value(by_name, f"{prefix}_net_profit"),
        nonrecurring_income=_value(by_name, f"{prefix}_nonrecurring_income") or 0.0,
        depletion=_value(by_name, f"{prefix}_depletion") or 0.0,
        depreciation=_value(by_name, f"{prefix}_depreciation") or 0.0,
        meals_entertainment_exclusion=_value(by_name, f"{prefix}_meals_entertainment_exclusion") or 0.0,
        business_use_of_home=_value(by_name, f"{prefix}_business_use_of_home") or 0.0,
        business_miles=_value(by_name, f"{prefix}_business_miles") or 0.0,
        amortization_casualty=_value(by_name, f"{prefix}_amortization_casualty") or 0.0,
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
    return sorted(indexes)


def _tax_year(by_name: dict[str, ExtractedField]) -> int | None:
    value = _value(by_name, "tax_year")
    return int(value) if value is not None else None


def _value(by_name: dict[str, ExtractedField], field_name: str) -> float | None:
    field = by_name.get(field_name)
    return field.value if field else None
