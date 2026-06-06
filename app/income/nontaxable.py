"""Pure non-taxable income + Social Security engine (spec section 3).

One source in, one qualifying monthly figure out, with a small taxable/eligible
breakdown where the method splits the amount. The gross-up rate defaults to 25%.
"""

from dataclasses import dataclass

from app.exceptions import InvalidNonTaxableInput
from app.schemas.nontaxable_inputs import (
    NonTaxableMethod,
    NonTaxableSource,
    SocialSecurityMethod,
    SocialSecuritySource,
)

# Fixed Social Security assumption: 15% of gross grossed up at 25% (spec 3).
_SS_TAXABLE_SHARE = 0.15
_SS_GROSS_UP = 0.25


@dataclass
class NonTaxableResult:
    monthly: float
    method: str
    taxable_monthly: float = 0.0
    eligible_monthly: float = 0.0


def compute_nontaxable_income(source: NonTaxableSource) -> NonTaxableResult:
    """Qualifying monthly non-taxable income for one source (spec 3)."""
    rate = source.gross_up_rate
    if source.method == NonTaxableMethod.gross_100:
        gross = _require(source.annual_gross, "annual_gross", source.method.value)
        monthly = round(gross / 12, 2)
        return NonTaxableResult(monthly, source.method.value, taxable_monthly=monthly)
    if source.method == NonTaxableMethod.total_adjusted:
        gross = _require(source.annual_gross, "annual_gross", source.method.value)
        taxable = _require(source.annual_taxable, "annual_taxable", source.method.value)
        taxable_mo = round(taxable / 12, 2)
        eligible_mo = round((gross - taxable) * (1 + rate) / 12, 2)
        return NonTaxableResult(
            round(taxable_mo + eligible_mo, 2),
            source.method.value,
            taxable_monthly=taxable_mo,
            eligible_monthly=eligible_mo,
        )
    return _current_monthly(source, rate)


def _current_monthly(source: NonTaxableSource, rate: float) -> NonTaxableResult:
    gross = _require(source.annual_gross, "annual_gross", source.method.value)
    taxable = _require(source.annual_taxable, "annual_taxable", source.method.value)
    current = _require(source.current_monthly, "current_monthly", source.method.value)
    taxable_ratio = _safe_div(taxable, gross)  # Excel IFERROR(...,0) on zero gross
    taxable_mo = current * taxable_ratio
    eligible_mo = current - taxable_mo
    return NonTaxableResult(
        round(taxable_mo + eligible_mo * (1 + rate), 2),
        source.method.value,
        taxable_monthly=round(taxable_mo, 2),
        eligible_monthly=round(eligible_mo * (1 + rate), 2),
    )


def compute_social_security(ss: SocialSecuritySource) -> NonTaxableResult:
    """Qualifying monthly Social Security income without taxation docs (spec 3)."""
    gross = _require(ss.annual_gross, "annual_gross", ss.method.value)
    if ss.method == SocialSecurityMethod.gross_100:
        monthly = round(gross / 12, 2)
        return NonTaxableResult(monthly, ss.method.value, taxable_monthly=monthly)
    gross_up = gross * _SS_TAXABLE_SHARE * _SS_GROSS_UP
    return NonTaxableResult(
        round((gross + gross_up) / 12, 2),
        ss.method.value,
        taxable_monthly=round(gross / 12, 2),
        eligible_monthly=round(gross_up / 12, 2),
    )


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _require(value: float | None, name: str, method: str) -> float:
    if value is None:
        raise InvalidNonTaxableInput(f"{method} requires {name}")
    return value
