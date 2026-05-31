from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.borrower import BorrowerResponse
from app.schemas.income_stream import IncomeStreamResponse
from app.schemas.extraction import ExtractedField


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    document_id: UUID
    case_id: UUID | None
    income_stream_id: UUID | None
    doc_type: str
    extracted_fields: list[ExtractedField]
    annual_income: float | None
    confidence: str | None
    notes: str | None
    created_at: datetime


class CaseSummaryResponse(BaseModel):
    case_id: UUID
    total_annual_income: float
    borrowers: list[BorrowerResponse] = Field(default_factory=list)
    income_streams: list[IncomeStreamResponse] = Field(default_factory=list)
    results: list[ResultResponse]
    sources: list[ExtractedField]
