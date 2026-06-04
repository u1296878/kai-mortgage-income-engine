"""Pure employment qualifying-income engine (spec section 2).

Five buckets — base pay plus four variable buckets — each blended months-weighted
(`Sum earnings / Sum months`, NOT an average of period monthlies), then summed.
"""

from dataclasses import dataclass

from app.exceptions import InvalidEmploymentInput
from app.income.dates import months_between
from app.income.pay_frequency import rate_of_pay_monthly
from app.schemas.income_inputs import BasePay, EmploymentInput, VariableBucket


@dataclass
class PeriodResult:
    """Per-period breakdown for review (spec 2.1). `pct_change` is informational."""

    months: float
    monthly: float
    pct_change: float | None


@dataclass
class BucketResult:
    qualifying_monthly: float
    rate_of_pay_monthly: float
    periods: list[PeriodResult]


@dataclass
class EmploymentResult:
    base_pay: BucketResult
    overtime: BucketResult
    bonus: BucketResult
    commission: BucketResult
    other: BucketResult
    total_monthly: float


def compute_employment_income(employment: EmploymentInput) -> EmploymentResult:
    """Total qualifying monthly income with a reviewable per-bucket breakdown."""
    base = _base_pay(employment.base_pay)
    overtime = _variable_bucket(employment.overtime, "overtime")
    bonus = _variable_bucket(employment.bonus, "bonus")
    commission = _variable_bucket(employment.commission, "commission")
    other = _variable_bucket(employment.other, "other")
    total = round(
        base.qualifying_monthly
        + overtime.qualifying_monthly
        + bonus.qualifying_monthly
        + commission.qualifying_monthly
        + other.qualifying_monthly,
        2,
    )
    return EmploymentResult(
        base_pay=base,
        overtime=overtime,
        bonus=bonus,
        commission=commission,
        other=other,
        total_monthly=total,
    )


def _safe_div(numerator: float, denominator: float) -> float:
    # Excel IFERROR(...,0): divide-by-zero yields 0, never a crash.
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _period_results(periods) -> list[PeriodResult]:
    """Per-period monthly earnings and trend (spec 2.1), in input order."""
    monthlies = []
    for period in periods:
        months = months_between(period.date_from, period.date_through)
        monthlies.append((months, round(_safe_div(period.total_earnings, months), 2)))
    results = []
    for index, (months, monthly) in enumerate(monthlies):
        if index + 1 < len(monthlies):
            prior_monthly = monthlies[index + 1][1]
            pct = round(_safe_div(monthly - prior_monthly, abs(prior_monthly)) * 100, 2)
        else:
            pct = None
        results.append(PeriodResult(months=months, monthly=monthly, pct_change=pct))
    return results


def _blend(periods, annualize_ytd: bool) -> float:
    """Months-weighted blend of the selected periods (spec 2.2/2.3).

    Period index 0 is the YTD row; when annualized its months are forced to 12.
    """
    total_earnings = 0.0
    total_months = 0.0
    for index, period in enumerate(periods):
        if not period.included:
            continue
        if index == 0 and annualize_ytd:
            months = 12.0
        else:
            months = months_between(period.date_from, period.date_through)
        total_earnings += period.total_earnings
        total_months += months
    return round(_safe_div(total_earnings, total_months), 2)


def _variable_bucket(bucket: VariableBucket, name: str) -> BucketResult:
    annualize = _resolve_ay_toggle(bucket, name)
    return BucketResult(
        qualifying_monthly=_blend(bucket.periods, annualize),
        rate_of_pay_monthly=0.0,
        periods=_period_results(bucket.periods),
    )


def _resolve_ay_toggle(bucket: VariableBucket, name: str) -> bool:
    """Exactly one of A/Y must be set (spec 2.3). Returns True when annualizing."""
    annualize = bool(bucket.annualize)
    use_ytd = bool(bucket.use_ytd)
    if annualize == use_ytd:
        raise InvalidEmploymentInput(
            f"{name}: exactly one of annualize (A) / use_ytd (Y) must be set"
        )
    return annualize


def _base_pay(base: BasePay) -> BucketResult:
    blend = _blend(base.periods, annualize_ytd=False)  # base pay has no A/Y toggle
    rop = 0.0
    if base.rate_line_included:
        if base.rate is None or base.pay_frequency is None:
            raise InvalidEmploymentInput("Base pay rate line requires rate and pay_frequency")
        rop = round(rate_of_pay_monthly(base.rate, base.pay_frequency, base.hours_weekly), 2)
    return BucketResult(
        qualifying_monthly=round(blend + rop, 2),
        rate_of_pay_monthly=rop,
        periods=_period_results(base.periods),
    )
