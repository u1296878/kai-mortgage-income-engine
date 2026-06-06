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


def test_two_year_average_is_months_weighted_and_excludes_toggled_off_year():
    source = ScheduleDInput(
        years=[
            ScheduleDYear(months=12, recurring_capital_gains=24000),
            ScheduleDYear(months=6, recurring_capital_gains=18000, included=False),
        ]
    )

    result = compute_schedule_d(source)

    assert result.qualifying_monthly == 2000.00


def test_excluded_year_drops_out_without_requiring_line_items():
    source = ScheduleDInput(
        years=[
            ScheduleDYear(months=12, recurring_capital_gains=24000),
            ScheduleDYear(months=6, included=False),
        ]
    )

    result = compute_schedule_d(source)

    assert result.years[1].annual_subtotal == 0.00
    assert result.qualifying_monthly == 2000.00


def test_two_year_average_uses_included_months():
    source = ScheduleDInput(
        years=[
            ScheduleDYear(months=12, recurring_capital_gains=24000),
            ScheduleDYear(months=6, recurring_capital_gains=18000),
        ]
    )

    result = compute_schedule_d(source)

    assert result.qualifying_monthly == 2333.33


def test_loss_passes_through_negative():
    source = ScheduleERoyaltyInput(
        years=[
            ScheduleERoyaltyYear(
                royalty_income=1000,
                total_expenses=5000,
                depreciation_depletion=0,
            )
        ]
    )

    result = compute_schedule_e_royalty(source)

    assert result.years[0].annual_subtotal == -4000.00
    assert result.qualifying_monthly == -333.33


def test_zero_included_months_guards_divide_by_zero():
    source = ScheduleDInput(
        years=[ScheduleDYear(months=0, recurring_capital_gains=6000)]
    )

    result = compute_schedule_d(source)

    assert result.qualifying_monthly == 0.00


@pytest.mark.parametrize(
    ("source", "compute"),
    [
        (ScheduleBInput(years=[ScheduleBYear(recurring_interest=100)]), compute_schedule_b),
        (ScheduleCInput(years=[schedule_c_year(net_profit=None)]), compute_schedule_c),
        (ScheduleDInput(years=[ScheduleDYear()]), compute_schedule_d),
        (
            ScheduleERoyaltyInput(years=[ScheduleERoyaltyYear(royalty_income=100)]),
            compute_schedule_e_royalty,
        ),
        (ScheduleFInput(years=[ScheduleFYear(net_profit=100)]), compute_schedule_f),
    ],
)
def test_missing_required_line_items_raise_invalid_input(source, compute):
    with pytest.raises(InvalidSelfEmploymentInput):
        compute(source)
