"""Annual subtotals for self-employment personal schedules (spec section 5.2)."""

from app.exceptions import InvalidSelfEmploymentInput
from app.schemas.self_employment_inputs import (
    ScheduleBYear,
    ScheduleCYear,
    ScheduleDYear,
    ScheduleERoyaltyYear,
    ScheduleFYear,
)

_MILEAGE_DEPRECIATION = {2025: 0.33, 2024: 0.30, 2023: 0.28}


def schedule_b_annual_subtotal(year: ScheduleBYear) -> float:
    return round(
        _required(year.recurring_interest, "recurring_interest")
        + _required(year.recurring_dividends, "recurring_dividends"),
        2,
    )


def schedule_c_annual_subtotal(year: ScheduleCYear) -> float:
    mileage_depreciation = _mileage_depreciation(year)
    return round(
        _required(year.net_profit, "net_profit")
        - _required(year.nonrecurring_income, "nonrecurring_income")
        + _required(year.depletion, "depletion")
        + _required(year.depreciation, "depreciation")
        - _required(
            year.meals_entertainment_exclusion,
            "meals_entertainment_exclusion",
        )
        + _required(year.business_use_of_home, "business_use_of_home")
        + mileage_depreciation
        + _required(year.amortization_casualty, "amortization_casualty")
        + _optional(year.w2_self_employment_income),
        2,
    )


def schedule_d_annual_subtotal(year: ScheduleDYear) -> float:
    return round(_required(year.recurring_capital_gains, "recurring_capital_gains"), 2)


def schedule_e_royalty_annual_subtotal(year: ScheduleERoyaltyYear) -> float:
    return round(
        _required(year.royalty_income, "royalty_income")
        - _required(year.total_expenses, "total_expenses")
        + _required(year.depreciation_depletion, "depreciation_depletion"),
        2,
    )


def schedule_f_annual_subtotal(year: ScheduleFYear) -> float:
    return round(
        _required(year.net_profit, "net_profit")
        + _required(year.nontax_coop_ccc_payments, "nontax_coop_ccc_payments")
        + _required(year.nonrecurring_loss, "nonrecurring_loss")
        - _required(year.nonrecurring_income, "nonrecurring_income")
        + _required(year.depreciation, "depreciation")
        + _required(
            year.amortization_casualty_depletion,
            "amortization_casualty_depletion",
        )
        + _required(year.business_use_of_home, "business_use_of_home"),
        2,
    )


def _mileage_depreciation(year: ScheduleCYear) -> float:
    miles = _required(year.business_miles, "business_miles")
    if miles == 0:
        return 0.0
    tax_year = year.tax_year
    if tax_year not in _MILEAGE_DEPRECIATION:
        raise InvalidSelfEmploymentInput(f"Unknown mileage depreciation year: {tax_year}")
    return miles * _MILEAGE_DEPRECIATION[tax_year]


def _required(value: float | None, name: str) -> float:
    if value is None:
        raise InvalidSelfEmploymentInput(f"{name} is required")
    return value


def _optional(value: float | None) -> float:
    if value is None:
        return 0.0
    return value
