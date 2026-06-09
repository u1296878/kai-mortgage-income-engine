"""Unified API schemas for self-employment calculations."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SelfEmploymentCalculationRequest(BaseModel):
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)


class SelfEmploymentCalculationCreate(SelfEmploymentCalculationRequest):
    borrower_id: UUID | None = None
    label: str | None = None
    included: bool = True


class SelfEmploymentCalculationUpdate(BaseModel):
    included: bool


class SelfEmploymentResult(BaseModel):
    kind: str
    qualifying_monthly: float
    annual_income: float
    breakdown: dict[str, Any]


class SelfEmploymentCalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    borrower_id: UUID | None
    label: str | None
    kind: str
    qualifying_monthly: float
    annual_income: float
    included: bool
    source_document_id: UUID | None
    source_business_key: str | None
    breakdown: dict[str, Any]
    created_at: datetime
