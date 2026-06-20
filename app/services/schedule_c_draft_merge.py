"""Merge extracted Schedule C years into saved self-employment drafts."""

from typing import Any

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.models.self_employment_calculation import SelfEmploymentCalculation
from app.repositories import self_employment_calculation_repo
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear
from app.schemas.self_employment_results import SelfEmploymentCalculationRequest
from app.services.schedule_c_business_match import (
    ScheduleCBusinessIdentity,
    business_names_match,
    is_single_business_key,
    source_key_name,
)
from app.services.self_employment_income_service import run_self_employment_engine


def matching_calculation(
    existing: list[SelfEmploymentCalculation],
    identity: ScheduleCBusinessIdentity,
) -> SelfEmploymentCalculation | None:
    candidates = [calc for calc in existing if calc.kind == "schedule_c"]
    for calculation in candidates:
        if calculation.source_business_key == identity.source_key:
            return calculation
    if identity.normalized_name:
        for calculation in candidates:
            if business_names_match(
                identity.normalized_name,
                source_key_name(calculation.source_business_key),
            ):
                return calculation
    if identity.source_key == "schedule_c_single_business":
        singles = [calc for calc in candidates if is_single_business_key(calc.source_business_key)]
        if len(singles) == 1:
            return singles[0]
    return None


def merge_year(
    db: Session,
    calculation: SelfEmploymentCalculation,
    identity: ScheduleCBusinessIdentity,
    year: ScheduleCYear,
) -> SelfEmploymentCalculation | None:
    source = ScheduleCInput.model_validate(calculation.inputs["payload"])
    if _has_year(source, year.tax_year) or len(source.years) >= 2:
        return None
    request = SelfEmploymentCalculationRequest(
        kind="schedule_c",
        payload=ScheduleCInput(years=[*source.years, year]).model_dump(mode="json"),
    )
    result = run_self_employment_engine(request)
    calculation.inputs = request.model_dump(mode="json")
    calculation.qualifying_monthly = result.qualifying_monthly
    calculation.annual_income = result.annual_income
    calculation.breakdown = with_review_flags(result.breakdown, identity.review_flags)
    calculation.source_business_key = identity.source_key
    if calculation.label is None or calculation.label.startswith("Schedule C business"):
        calculation.label = identity.label
    saved = self_employment_calculation_repo.update(db, calculation)
    log_event(
        "schedule_c_self_employment_draft_updated",
        {"calculation_id": saved.id, "source_key": identity.source_key},
    )
    return saved


def with_review_flags(
    breakdown: dict[str, Any],
    review_flags: list[str],
) -> dict[str, Any]:
    if not review_flags:
        return breakdown
    merged = {**breakdown}
    existing_flags = list(merged.get("review_flags", []))
    merged["review_flags"] = sorted({*existing_flags, *review_flags})
    return merged


def _has_year(source: ScheduleCInput, tax_year: int | None) -> bool:
    if tax_year is None:
        return False
    return any(year.tax_year == tax_year for year in source.years)
