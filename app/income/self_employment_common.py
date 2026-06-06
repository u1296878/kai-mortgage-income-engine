"""Shared self-employment averaging helpers (spec section 5.6)."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, TypeVar


class SelfEmploymentYearLike(Protocol):
    months: float
    included: bool


@dataclass
class SelfEmploymentYearResult:
    months: float
    annual_subtotal: float
    included: bool


YearT = TypeVar("YearT", bound=SelfEmploymentYearLike)


def build_year_results(
    years: Sequence[YearT],
    subtotal_fn: Callable[[YearT], float],
) -> list[SelfEmploymentYearResult]:
    return [
        SelfEmploymentYearResult(
            months=year.months,
            annual_subtotal=subtotal_fn(year) if year.included else 0.0,
            included=year.included,
        )
        for year in years
    ]


def qualifying_monthly(years: Sequence[SelfEmploymentYearResult]) -> float:
    included = [year for year in years if year.included]
    months = sum(year.months for year in included)
    if months == 0:
        return 0.0
    return sum(year.annual_subtotal for year in included) / months
