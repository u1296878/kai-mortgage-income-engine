"""API response models mirroring the employment engine dataclasses.

The engine stays pure (returns dataclasses); these give the API a typed contract.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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


class EmploymentCalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    borrower_id: UUID | None
    label: str | None
    total_monthly: float
    annual_income: float
    breakdown: EmploymentResult
    created_at: datetime
