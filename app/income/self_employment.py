"""Pure self-employment personal schedule engine (spec sections 5.2, 5.6)."""

from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.self_employment_inputs import (
    ScheduleBInput,
    ScheduleCInput,
    ScheduleDInput,
    ScheduleERoyaltyInput,
    ScheduleFInput,
    SelfEmploymentYear,
)
from app.income.self_employment_schedules import (
    schedule_b_annual_subtotal,
    schedule_c_annual_subtotal,
    schedule_d_annual_subtotal,
    schedule_e_royalty_annual_subtotal,
    schedule_f_annual_subtotal,
)


@dataclass
class SelfEmploymentYearResult:
    months: float
    annual_subtotal: float
    included: bool


@dataclass
class SelfEmploymentResult:
    qualifying_monthly: float
    schedule: str
    years: list[SelfEmploymentYearResult]


def compute_schedule_b(source: ScheduleBInput) -> SelfEmploymentResult:
    return _compute("schedule_b", source.years, schedule_b_annual_subtotal)


def compute_schedule_c(source: ScheduleCInput) -> SelfEmploymentResult:
    return _compute("schedule_c", source.years, schedule_c_annual_subtotal)


def compute_schedule_d(source: ScheduleDInput) -> SelfEmploymentResult:
    return _compute("schedule_d", source.years, schedule_d_annual_subtotal)


def compute_schedule_e_royalty(source: ScheduleERoyaltyInput) -> SelfEmploymentResult:
    return _compute("schedule_e_royalty", source.years, schedule_e_royalty_annual_subtotal)


def compute_schedule_f(source: ScheduleFInput) -> SelfEmploymentResult:
    return _compute("schedule_f", source.years, schedule_f_annual_subtotal)


def _compute(
    schedule: str,
    years: list[SelfEmploymentYear],
    subtotal_fn: Callable[[SelfEmploymentYear], float],
) -> SelfEmploymentResult:
    year_results = [
        SelfEmploymentYearResult(
            months=year.months,
            annual_subtotal=subtotal_fn(year) if year.included else 0.0,
            included=year.included,
        )
        for year in years
    ]
    qualifying = _qualifying_monthly(year_results)
    return SelfEmploymentResult(
        qualifying_monthly=round(qualifying, 2),
        schedule=schedule,
        years=year_results,
    )


def _qualifying_monthly(years: list[SelfEmploymentYearResult]) -> float:
    included = [year for year in years if year.included]
    months = sum(year.months for year in included)
    if months == 0:
        return 0.0
    return sum(year.annual_subtotal for year in included) / months
