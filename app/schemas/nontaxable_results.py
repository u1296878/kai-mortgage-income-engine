"""API response models for non-taxable and Social Security calculations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NonTaxableResult(BaseModel):
    monthly: float
    method: str
    taxable_monthly: float = 0.0
    eligible_monthly: float = 0.0


class NonTaxableCalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    borrower_id: UUID | None
    label: str | None
    kind: str
    monthly: float
    annual_income: float
    breakdown: NonTaxableResult
    created_at: datetime
