"""Pure rental qualifying-income engine (spec section 4).

One property in, one qualifying monthly figure out, with a reviewable per-year
breakdown. Rental losses are legitimate and flow through as negative numbers.
"""

from dataclasses import dataclass

from app.exceptions import InvalidRentalInput
from app.schemas.rental_inputs import (
    PropertyClass,
    RentalMethod,
    RentalProperty,
    ScheduleEYear,
)


@dataclass
class RentalYearResult:
    months: float
    annual_net: float
    monthly_gross: float


@dataclass
class RentalResult:
    qualifying_monthly: float
    property_class: str
    method: str
    years: list[RentalYearResult]


def months_from_fair_rental_days(days: float | None) -> float:
    """Months in service from Schedule E fair-rental days (spec 4.1)."""
    if days is None:
        return 12.0
    return min(days / 30, 12)


def compute_rental_income(property_input: RentalProperty) -> RentalResult:
    """Qualifying monthly rental income for a single property (spec 4)."""
    if property_input.method == RentalMethod.lease:
        return _lease(property_input)
    return _schedule_e(property_input)


def _safe_div(numerator: float, denominator: float) -> float:
    # Excel IFERROR(...,0): zero months in service yields 0, never a crash.
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _annual_net(year: ScheduleEYear) -> float:
    # Losses (negative net) are legitimate and must pass through unclamped.
    return (
        year.rents_received
        - year.total_expenses
        + year.insurance
        + year.mortgage_interest
        + year.taxes
        + year.depreciation_depletion
        + year.hoa_addback
        + year.casualty_one_time
    )


def _year_result(year: ScheduleEYear) -> RentalYearResult:
    months = min(year.months_in_service, 12)
    annual_net = _annual_net(year)
    return RentalYearResult(
        months=months,
        annual_net=annual_net,
        monthly_gross=round(_safe_div(annual_net, months), 2),
    )


def _schedule_e(property_input: RentalProperty) -> RentalResult:
    if not property_input.schedule_e_years:
        raise InvalidRentalInput("Schedule E method requires at least one year")
    years = [_year_result(year) for year in property_input.schedule_e_years]
    if property_input.property_class == PropertyClass.investment:
        qualifying = _investment_average(years, _required_pitia(property_input))
    else:
        qualifying = _primary_average(years)
    return _result(property_input, round(qualifying, 2), years)


def _primary_average(years: list[RentalYearResult]) -> float:
    # Primary 2-4 unit: annual-weighted gross average (spec 4.1).
    total_annual = sum(year.annual_net for year in years)
    total_months = sum(year.months for year in years)
    return _safe_div(total_annual, total_months)


def _investment_average(years: list[RentalYearResult], monthly_pitia: float) -> float:
    # Investment: months-weighted average of net monthly (gross - PITIA) (spec 4.1).
    total_months = sum(year.months for year in years)
    weighted_net = sum(
        year.months * (_safe_div(year.annual_net, year.months) - monthly_pitia)
        for year in years
    )
    return _safe_div(weighted_net, total_months)


def _lease(property_input: RentalProperty) -> RentalResult:
    if property_input.gross_monthly_rent is None:
        raise InvalidRentalInput("Lease method requires gross_monthly_rent")
    adjusted = property_input.gross_monthly_rent * (1 - property_input.vacancy_factor)
    if property_input.property_class == PropertyClass.investment:
        adjusted -= _required_pitia(property_input)
    return _result(property_input, round(adjusted, 2), [])


def _required_pitia(property_input: RentalProperty) -> float:
    if property_input.monthly_pitia is None:
        raise InvalidRentalInput("Investment property requires monthly_pitia")
    return property_input.monthly_pitia


def _result(
    property_input: RentalProperty,
    qualifying_monthly: float,
    years: list[RentalYearResult],
) -> RentalResult:
    return RentalResult(
        qualifying_monthly=qualifying_monthly,
        property_class=property_input.property_class.value,
        method=property_input.method.value,
        years=years,
    )
