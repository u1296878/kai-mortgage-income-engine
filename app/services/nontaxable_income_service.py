"""Stateless service: run non-taxable/SS engines and map to the API contract."""

from dataclasses import asdict

from app.audit.logger import log_event
from app.exceptions import InvalidNonTaxableInput
from app.income.nontaxable import compute_nontaxable_income, compute_social_security
from app.schemas.nontaxable_inputs import (
    NonTaxableCalculationRequest,
    NonTaxableKind,
    NonTaxableSource,
    SocialSecuritySource,
)
from app.schemas.nontaxable_results import NonTaxableResult


def calculate_nontaxable_income(
    request: NonTaxableCalculationRequest,
) -> NonTaxableResult:
    result = _dispatch(request)
    log_event(
        "nontaxable_income_calculated",
        {"kind": request.kind.value, "monthly": result.monthly},
    )
    return NonTaxableResult.model_validate(asdict(result))


def _dispatch(request: NonTaxableCalculationRequest):
    if request.kind == NonTaxableKind.income:
        return compute_nontaxable_income(_require_income(request.income))
    return compute_social_security(_require_social_security(request.social_security))


def _require_income(source: NonTaxableSource | None) -> NonTaxableSource:
    if source is None:
        raise InvalidNonTaxableInput("income source is required for kind=income")
    return source


def _require_social_security(
    source: SocialSecuritySource | None,
) -> SocialSecuritySource:
    if source is None:
        raise InvalidNonTaxableInput(
            "social_security source is required for kind=social_security",
        )
    return source
