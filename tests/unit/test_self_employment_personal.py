import pytest

from app.exceptions import InvalidSelfEmploymentInput
from app.income.self_employment import (
    compute_schedule_b,
    compute_schedule_c,
    compute_schedule_d,
    compute_schedule_e_royalty,
    compute_schedule_f,
)
from app.schemas.self_employment_inputs import (
    ScheduleBInput,
    ScheduleBYear,
    ScheduleCInput,
    ScheduleCYear,
    ScheduleDInput,
    ScheduleDYear,
    ScheduleERoyaltyInput,
    ScheduleERoyaltyYear,
    ScheduleFInput,
    ScheduleFYear,
)


def schedule_c_year(**overrides):
    values = {
        "tax_year": 2025,
        "net_profit": 50000,
        "nonrecurring_income": 2000,
        "depletion": 500,
        "depreciation": 3000,
        "meals_entertainment_exclusion": 1000,
        "business_use_of_home": 1500,
        "business_miles": 0,
        "amortization_casualty": 700,
    }
    values.update(overrides)
    return ScheduleCYear(**values)


def test_schedule_c_sole_prop_subtotal_adds_back_allowed_items():
    source = ScheduleCInput(years=[schedule_c_year()])

    result = compute_schedule_c(source)

    assert result.years[0].annual_subtotal == 52700.00
    assert result.qualifying_monthly == 4391.67


def test_schedule_c_single_member_llc_adds_w2_self_employment_income():
    source = ScheduleCInput(
        years=[schedule_c_year(w2_self_employment_income=12000)]
    )

    result = compute_schedule_c(source)

    assert result.years[0].annual_subtotal == 64700.00


def test_schedule_c_mileage_uses_tax_year_depreciation_rate():
    source = ScheduleCInput(
        years=[
            schedule_c_year(tax_year=2025, business_miles=1000),
            schedule_c_year(tax_year=2024, business_miles=1000),
        ]
    )

    result = compute_schedule_c(source)

    assert result.years[0].annual_subtotal == 53030.00
    assert result.years[1].annual_subtotal == 53000.00


def test_schedule_c_unknown_mileage_year_raises_invalid_input():
    source = ScheduleCInput(years=[schedule_c_year(tax_year=2022, business_miles=100)])

    with pytest.raises(InvalidSelfEmploymentInput):
        compute_schedule_c(source)


def test_schedule_b_interest_and_dividends_subtotal():
    source = ScheduleBInput(
        years=[ScheduleBYear(recurring_interest=1200, recurring_dividends=800)]
    )

    result = compute_schedule_b(source)

    assert result.years[0].annual_subtotal == 2000.00
    assert result.qualifying_monthly == 166.67


def test_schedule_d_recurring_capital_gains_subtotal():
    source = ScheduleDInput(years=[ScheduleDYear(recurring_capital_gains=6000)])

    result = compute_schedule_d(source)

    assert result.years[0].annual_subtotal == 6000.00


def test_schedule_e_royalty_subtotal_uses_royalty_expenses_and_depreciation():
    source = ScheduleERoyaltyInput(
        years=[
            ScheduleERoyaltyYear(
                royalty_income=20000,
                total_expenses=5000,
                depreciation_depletion=1200,
            )
        ]
    )

    result = compute_schedule_e_royalty(source)

    assert result.years[0].annual_subtotal == 16200.00


def test_schedule_f_farm_subtotal_adds_back_allowed_items():
    source = ScheduleFInput(
        years=[
            ScheduleFYear(
                net_profit=40000,
                nontax_coop_ccc_payments=1000,
                nonrecurring_loss=2500,
                nonrecurring_income=1500,
                depreciation=3000,
                amortization_casualty_depletion=400,
                business_use_of_home=600,
            )
        ]
    )

    result = compute_schedule_f(source)

    assert result.years[0].annual_subtotal == 46000.00
