import pytest

from app.exceptions import InvalidEmploymentInput
from app.income.pay_frequency import PAY_FREQUENCY, rate_of_pay_monthly


def test_table_holds_standard_periods_per_year():
    assert PAY_FREQUENCY["weekly"] == 52
    assert PAY_FREQUENCY["biweekly"] == 26
    assert PAY_FREQUENCY["semimonthly"] == 24
    assert PAY_FREQUENCY["monthly"] == 12


def test_non_hourly_uses_periods_per_year():
    monthly = rate_of_pay_monthly(2000.0, "biweekly", None)

    assert monthly == pytest.approx(2000.0 * 26 / 12)


def test_hourly_uses_weekly_hours_times_fifty_two():
    monthly = rate_of_pay_monthly(25.0, "hourly", 40.0)

    assert monthly == pytest.approx(25.0 * 40.0 * 52 / 12)


def test_varies_frequency_yields_zero_rate_of_pay():
    monthly = rate_of_pay_monthly(5000.0, "varies", None)

    assert monthly == 0.0


def test_unknown_frequency_raises_invalid_employment_input():
    with pytest.raises(InvalidEmploymentInput):
        rate_of_pay_monthly(2000.0, "fortnightly", None)


def test_hourly_without_hours_raises_invalid_employment_input():
    with pytest.raises(InvalidEmploymentInput):
        rate_of_pay_monthly(25.0, "hourly", None)
