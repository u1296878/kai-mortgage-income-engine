"""Pydantic input models for the income calc engine (spec 2.5).

The variable buckets carry two booleans, `annualize` (worksheet "A") and
`use_ytd` (worksheet "Y"), modelling the two YTD-row checkboxes from spec 2.3.
Exactly one must be set; the engine raises on both-set / both-unset.
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel


class EmploymentPeriod(BaseModel):
    date_from: date
    date_through: date
    total_earnings: float
    included: bool = True


class VariableBucket(BaseModel):
    """OT, bonus, commission, other — periods ordered YTD, prior, prior-prior."""

    periods: list[EmploymentPeriod]
    annualize: bool | None = None  # worksheet "A" toggle (spec 2.3)
    use_ytd: bool | None = None  # worksheet "Y" toggle (spec 2.3)


class BasePay(BaseModel):
    periods: list[EmploymentPeriod]
    rate: float | None = None
    pay_frequency: str | None = None  # key into PAY_FREQUENCY
    hours_weekly: float | None = None
    rate_line_included: bool = False


class EmploymentInput(BaseModel):
    base_pay: BasePay
    overtime: VariableBucket
    bonus: VariableBucket
    commission: VariableBucket
    other: VariableBucket


class EmploymentCalculationCreate(EmploymentInput):
    """Save request: a full EmploymentInput plus optional case-binding metadata."""

    borrower_id: UUID | None = None
    label: str | None = None
