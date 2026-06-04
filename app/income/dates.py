"""Fractional month math shared by every income period (spec 1.1)."""

from calendar import monthrange
from datetime import date


def months_between(date_from: date, date_through: date) -> float:
    """Whole months strictly between, plus partial first and last months.

    Mirrors the worksheet `K` column exactly (spec 1.1):
    a full calendar year is 12.0; `2026-01-01`..`2026-04-15` is 3.5.
    """
    whole = (
        (date_through.year - date_from.year) * 12
        - 12
        + (12 - date_from.month)
        + date_through.month
        - 1
    )
    from_days = monthrange(date_from.year, date_from.month)[1]
    through_days = monthrange(date_through.year, date_through.month)[1]
    first = (from_days - date_from.day + 1) / from_days
    last = date_through.day / through_days
    return whole + first + last
