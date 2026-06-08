"""API response models mirroring the rental engine dataclasses (spec section 4).

The engine stays pure (returns dataclasses); these give the API a typed contract.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RentalYearResult(BaseModel):
    months: float
    annual_net: float
    monthly_gross: float


class RentalResult(BaseModel):
    qualifying_monthly: float
    property_class: str
    method: str
    years: list[RentalYearResult]


class RentalCalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    borrower_id: UUID | None
    label: str | None
    inputs: dict
    qualifying_monthly: float
    annual_income: float
    included: bool
    source_document_id: UUID | None
    source_property_key: str | None
    breakdown: RentalResult
    created_at: datetime
