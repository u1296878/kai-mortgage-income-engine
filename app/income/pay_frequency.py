"""Pay-frequency periods/year table and rate-of-pay helper (spec 1.2, 2.2)."""

from app.exceptions import InvalidEmploymentInput

HOURLY = "hourly"

# Selection key -> pay periods per year (spec 1.2 `VLKP_PAY_FREQ`).
# Hourly is special-cased in rate_of_pay_monthly; "varies" disables rate-of-pay
# by yielding 0 periods/year (rate-of-pay not usable).
PAY_FREQUENCY: dict[str, int] = {
    HOURLY: 0,
    "weekly": 52,
    "biweekly": 26,
    "semimonthly": 24,
    "monthly": 12,
    "quarterly": 4,
    "semiannually": 2,
    "annually": 1,
    "varies": 0,
}


def rate_of_pay_monthly(
    rate: float,
    pay_frequency: str,
    hours_weekly: float | None,
) -> float:
    """Monthly base pay from a rate-of-pay line (spec 2.2).

    Hourly: rate * hours_weekly * 52 / 12. Otherwise: rate * periods/year / 12.
    """
    if pay_frequency not in PAY_FREQUENCY:
        raise InvalidEmploymentInput(f"Unknown pay frequency: {pay_frequency!r}")
    if pay_frequency == HOURLY:
        if hours_weekly is None:
            raise InvalidEmploymentInput("Hourly rate-of-pay requires hours_weekly")
        return (rate * hours_weekly * 52) / 12
    return (rate * PAY_FREQUENCY[pay_frequency]) / 12
