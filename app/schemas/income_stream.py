from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.income_stream_type import IncomeStreamType


class IncomeStreamCreate(BaseModel):
    name: str
    stream_type: IncomeStreamType
    notes: str | None = None


class IncomeStreamUpdate(BaseModel):
    name: str | None = None
    stream_type: IncomeStreamType | None = None
    notes: str | None = None


class IncomeStreamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    broker_id: UUID
    name: str
    stream_type: IncomeStreamType
    annual_income: float | None
    confidence: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class IncomeStreamWithResults(IncomeStreamResponse):
    result_ids: list[UUID]
