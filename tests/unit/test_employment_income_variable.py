from datetime import date

import pytest

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
    return VariableBucket(periods=[], use_ytd=True)


def employment(base_pay, **buckets):
    return EmploymentInput(
        base_pay=base_pay,
        overtime=buckets.get("overtime", empty_bucket()),
        bonus=buckets.get("bonus", empty_bucket()),
        commission=buckets.get("commission", empty_bucket()),
        other=buckets.get("other", empty_bucket()),
    )


def test_variable_bucket_year_to_date_uses_actual_months():
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],
        use_ytd=True,
    )

    result = compute_employment_income(employment(_base(), overtime=overtime))

    assert result.overtime.qualifying_monthly == 2000.00


def test_variable_bucket_annualize_forces_twelve_months():
    overtime = VariableBucket(
        periods=[period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],
        annualize=True,
    )

    result = compute_employment_income(employment(_base(), overtime=overtime))

    assert result.overtime.qualifying_monthly == 500.00


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
