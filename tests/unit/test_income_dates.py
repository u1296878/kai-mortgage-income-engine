from datetime import date

import pytest

from app.income.dates import months_between


def test_full_calendar_year_is_twelve_months():
    months = months_between(date(2025, 1, 1), date(2025, 12, 31))

    assert months == 12.0


def test_spec_partial_year_example_is_three_and_a_half_months():
    months = months_between(date(2026, 1, 1), date(2026, 4, 15))

    assert months == 3.5


def test_leap_year_february_full_month_is_one_month():
    months = months_between(date(2024, 2, 1), date(2024, 2, 29))

    assert months == 1.0


def test_leap_year_february_partial_uses_twenty_nine_day_denominator():
    months = months_between(date(2024, 2, 15), date(2024, 2, 29))

    assert months == pytest.approx(15 / 29)


def test_partial_single_month_uses_day_fractions():
    months = months_between(date(2026, 1, 1), date(2026, 1, 15))

    assert months == pytest.approx(15 / 31)


def test_cross_year_range_sums_whole_and_partial_months():
    months = months_between(date(2024, 6, 15), date(2025, 3, 10))

    assert months == pytest.approx(8 + 16 / 30 + 10 / 31)
