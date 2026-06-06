"""API response models mirroring the employment engine dataclasses.

The engine stays pure (returns dataclasses); these give the API a typed contract.
"""

from pydantic import BaseModel


class PeriodResult(BaseModel):
    months: float
    monthly: float
    pct_change: float | None


class BucketResult(BaseModel):
    qualifying_monthly: float
    rate_of_pay_monthly: float
    periods: list[PeriodResult]


class EmploymentResult(BaseModel):
    base_pay: BucketResult
    overtime: BucketResult
    bonus: BucketResult
    commission: BucketResult
    other: BucketResult
    total_monthly: float
