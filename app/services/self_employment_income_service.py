"""Stateless service: dispatch self-employment engines by kind."""

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from pydantic import BaseModel, ValidationError

from app.audit.logger import log_event
from app.exceptions import InvalidSelfEmploymentInput
from app.income.self_employment import (
    compute_schedule_b,
    compute_schedule_c,
    compute_schedule_d,
    compute_schedule_e_royalty,
    compute_schedule_f,
)
from app.income.self_employment_entity import (
    compute_corporation,
    compute_partnership,
    compute_s_corporation,
)
from app.schemas.self_employment_entity_inputs import (
    CorporationInput,
    PartnershipInput,
    SCorpInput,
)
from app.schemas.self_employment_inputs import (
    ScheduleBInput,
    ScheduleCInput,
    ScheduleDInput,
    ScheduleERoyaltyInput,
    ScheduleFInput,
)
from app.schemas.self_employment_results import (
    SelfEmploymentCalculationRequest,
    SelfEmploymentResult,
)

ComputeFn = Callable[[Any], Any]
RegistryEntry = tuple[type[BaseModel], ComputeFn]

KIND_REGISTRY: dict[str, RegistryEntry] = {
    "schedule_b": (ScheduleBInput, compute_schedule_b),
    "schedule_c": (ScheduleCInput, compute_schedule_c),
    "schedule_d": (ScheduleDInput, compute_schedule_d),
    "schedule_e_royalty": (ScheduleERoyaltyInput, compute_schedule_e_royalty),
    "schedule_f": (ScheduleFInput, compute_schedule_f),
    "partnership": (PartnershipInput, compute_partnership),
    "s_corporation": (SCorpInput, compute_s_corporation),
    "corporation": (CorporationInput, compute_corporation),
}


def calculate_self_employment_income(
    request: SelfEmploymentCalculationRequest,
) -> SelfEmploymentResult:
    result = run_self_employment_engine(request)
    log_event(
        "self_employment_income_calculated",
        {"kind": result.kind, "qualifying_monthly": result.qualifying_monthly},
    )
    return result


def run_self_employment_engine(
    request: SelfEmploymentCalculationRequest,
) -> SelfEmploymentResult:
    input_model, compute = _registry_entry(request.kind)
    payload = _validate_payload(input_model, request.payload)
    result = compute(payload)
    return _normalize_result(request.kind, asdict(result))


def _registry_entry(kind: str) -> RegistryEntry:
    entry = KIND_REGISTRY.get(kind)
    if entry is None:
        raise InvalidSelfEmploymentInput(f"Unsupported self-employment kind: {kind}")
    return entry


def _validate_payload(
    input_model: type[BaseModel],
    payload: dict[str, Any],
) -> BaseModel:
    try:
        return input_model.model_validate(payload)
    except ValidationError as error:
        raise InvalidSelfEmploymentInput(str(error)) from error


def _normalize_result(kind: str, breakdown: dict[str, Any]) -> SelfEmploymentResult:
    monthly = breakdown["qualifying_monthly"]
    return SelfEmploymentResult(
        kind=kind,
        qualifying_monthly=monthly,
        annual_income=round(monthly * 12, 2),
        breakdown=breakdown,
    )
