"""Pure self-employment personal schedule engine (spec sections 5.2, 5.6)."""

from collections.abc import Callable
from dataclasses import dataclass

from app.income.self_employment_common import (
    SelfEmploymentYearResult,
    build_year_results,
    qualifying_monthly,
)
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
    year_results = build_year_results(years, subtotal_fn)
    qualifying = qualifying_monthly(year_results)
    return SelfEmploymentResult(
        qualifying_monthly=round(qualifying, 2),
        schedule=schedule,
        years=year_results,
    )
