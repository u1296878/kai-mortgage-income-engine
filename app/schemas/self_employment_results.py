"""Unified API schemas for self-employment calculations."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SelfEmploymentCalculationRequest(BaseModel):
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)


class SelfEmploymentCalculationCreate(SelfEmploymentCalculationRequest):
    borrower_id: UUID | None = None
    label: str | None = None


class SelfEmploymentResult(BaseModel):
    kind: str
    qualifying_monthly: float
    annual_income: float
    breakdown: dict[str, Any]
