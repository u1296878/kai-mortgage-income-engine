"""Build an engine input from a fixture's engine_input and return its monthly figure.

Read-only bridge between the JSON tie-out fixtures and the calc engines. Imports the
engine (never modifies it). Self-employment reuses the production KIND_REGISTRY so the
dispatch stays single-sourced.
"""

from __future__ import annotations

from typing import Any

from app.income.employment import compute_employment_income
from app.income.rental import compute_rental_income
from app.schemas.income_inputs import EmploymentInput
from app.schemas.rental_inputs import RentalProperty
from app.services.self_employment_income_service import KIND_REGISTRY


def compute_engine(worksheet: str, engine_input: dict[str, Any]) -> float:
    if worksheet == "employment":
        return _employment(engine_input)
    if worksheet == "rental":
        return compute_rental_income(RentalProperty.model_validate(engine_input)).qualifying_monthly
    if worksheet == "self_employment":
        model, compute = KIND_REGISTRY[engine_input["kind"]]
        result = compute(model.model_validate(engine_input["payload"]))
        return result.qualifying_monthly
    raise ValueError(f"Unknown tie-out worksheet: {worksheet}")


def _employment(engine_input: dict[str, Any]) -> float:
    # Variable buckets are required on EmploymentInput; default any omitted bucket to
    # a valid empty bucket (Y selected) so a base-pay-only scenario validates.
    filled = dict(engine_input)
    for bucket in ("overtime", "bonus", "commission", "other"):
        filled.setdefault(bucket, {"periods": [], "use_ytd": True})
    return compute_employment_income(EmploymentInput.model_validate(filled)).total_monthly
