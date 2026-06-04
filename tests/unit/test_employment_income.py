from datetime import date

import pytest
from pydantic import ValidationError

from app.exceptions import InvalidEmploymentInput
from app.income.employment import compute_employment_income
from app.schemas.income_inputs import (
    BasePay,
    EmploymentInput,
    EmploymentPeriod,
    VariableBucket,
)


def period(date_from, date_through, total, included=True):
    return EmploymentPeriod(
        date_from=date_from,
        date_through=date_through,
        total_earnings=total,
        included=included,
    )


def empty_bucket():
    # A valid-but-zero variable bucket for filling unused slots (Y selected).
    return VariableBucket(periods=[], use_ytd=True)


def employment(base_pay, **buckets):
    return EmploymentInput(
        base_pay=base_pay,
        overtime=buckets.get("overtime", empty_bucket()),
        bonus=buckets.get("bonus", empty_bucket()),
        commission=buckets.get("commission", empty_bucket()),
        other=buckets.get("other", empty_bucket()),
    )


def test_base_pay_blends_full_year_and_ytd_weighted_by_months():
    base = BasePay(
        periods=[
            period(date(2026, 1, 1), date(2026, 4, 15), 17500.0),  # 3.5 months
            period(date(2025, 1, 1), date(2025, 12, 31), 60000.0),  # 12 months
        ]
    )

    result = compute_employment_income(employment(base))

    assert result.base_pay.qualifying_monthly == 5000.00


def test_blend_weights_by_months_not_simple_average():
    base = BasePay(
        periods=[
            period(date(2026, 1, 1), date(2026, 3, 31), 36000.0),  # 3 mo, 12000/mo
            period(date(2025, 1, 1), date(2025, 12, 31), 120000.0),  # 12 mo, 10000/mo
        ]
    )

    result = compute_employment_income(employment(base))

    assert result.base_pay.qualifying_monthly == 10400.00
    assert result.base_pay.qualifying_monthly != 11000.00


def test_period_breakdown_surfaces_monthly_and_pct_change():
    base = BasePay(
        periods=[
            period(date(2026, 1, 1), date(2026, 3, 31), 36000.0),
            period(date(2025, 1, 1), date(2025, 12, 31), 120000.0),
        ]
    )

    result = compute_employment_income(employment(base))

    assert result.base_pay.periods[0].monthly == 12000.00
    assert result.base_pay.periods[0].pct_change == 20.00
    assert result.base_pay.periods[1].pct_change is None


def test_rate_of_pay_line_adds_to_base_blend():
    base = BasePay(
        periods=[period(date(2025, 1, 1), date(2025, 12, 31), 48000.0)],  # 4000/mo
        rate=20.0,
        pay_frequency="hourly",
        hours_weekly=40.0,
        rate_line_included=True,
    )

    result = compute_employment_income(employment(base))

    assert result.base_pay.rate_of_pay_monthly == 3466.67  # 20*40*52/12
    assert result.base_pay.qualifying_monthly == 7466.67  # 4000 + 3466.67


def test_rate_line_without_rate_raises_invalid_employment_input():
    base = BasePay(
        periods=[period(date(2025, 1, 1), date(2025, 12, 31), 48000.0)],
        pay_frequency="monthly",
        rate_line_included=True,
    )

    with pytest.raises(InvalidEmploymentInput):
        compute_employment_income(employment(base))


def test_variable_bucket_year_to_date_uses_actual_months():
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],  # 3 months
        use_ytd=True,
    )

    result = compute_employment_income(employment(_base(), overtime=overtime))

    assert result.overtime.qualifying_monthly == 2000.00  # 6000 / 3


def test_variable_bucket_annualize_forces_twelve_months():
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],
        annualize=True,
    )

    result = compute_employment_income(employment(_base(), overtime=overtime))

    assert result.overtime.qualifying_monthly == 500.00  # 6000 / 12


def test_both_annualize_and_ytd_set_raises_invalid_employment_input():
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],
        annualize=True,
        use_ytd=True,
    )

    with pytest.raises(InvalidEmploymentInput):
        compute_employment_income(employment(_base(), overtime=overtime))


def test_neither_annualize_nor_ytd_set_raises_invalid_employment_input():
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],
    )

    with pytest.raises(InvalidEmploymentInput):
        compute_employment_income(employment(_base(), overtime=overtime))


def test_missing_prior_year_blends_only_available_period():
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],
        use_ytd=True,
    )

    result = compute_employment_income(employment(_base(), overtime=overtime))

    assert result.overtime.qualifying_monthly == 2000.00


def test_all_periods_excluded_guards_divide_by_zero():
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0, included=False)],
        use_ytd=True,
    )

    result = compute_employment_income(employment(_base(), overtime=overtime))

    assert result.overtime.qualifying_monthly == 0.00


def test_missing_period_dates_fail_validation():
    with pytest.raises(ValidationError):
        EmploymentPeriod(total_earnings=1000.0)


def test_total_is_sum_of_all_bucket_qualifying_figures():
    base = BasePay(
        periods=[
            period(date(2026, 1, 1), date(2026, 4, 15), 17500.0),
            period(date(2025, 1, 1), date(2025, 12, 31), 60000.0),
        ]
    )
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],
        use_ytd=True,
    )

    result = compute_employment_income(employment(base, overtime=overtime))

    assert result.base_pay.qualifying_monthly == 5000.00
    assert result.overtime.qualifying_monthly == 2000.00
    assert result.total_monthly == 7000.00


def _base():
    return BasePay(periods=[period(date(2025, 1, 1), date(2025, 12, 31), 60000.0)])
