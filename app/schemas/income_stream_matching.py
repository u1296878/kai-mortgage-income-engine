from uuid import UUID

from pydantic import BaseModel

from app.models.income_stream_type import IncomeStreamType


class IncomeStreamMatchSuggestion(BaseModel):
    result_id: UUID
    stream_id: UUID | None = None
    stream_type: IncomeStreamType
    suggested_stream_name: str
    confidence: str
    reason: str
    can_auto_apply: bool
    action: str


class IncomeStreamMatchApplyRequest(BaseModel):
    force_reassign: bool = False


class IncomeStreamMatchApplyResponse(BaseModel):
    suggestions: list[IncomeStreamMatchSuggestion]
    applied_count: int
    created_stream_count: int
