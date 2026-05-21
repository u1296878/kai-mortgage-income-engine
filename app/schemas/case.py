from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.case_status import CaseStatus
from app.schemas.document import DocumentResponse


class CaseCreate(BaseModel):
    title: str
    broker_id: UUID


class CaseUpdate(BaseModel):
    title: str | None = None
    status: CaseStatus | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    broker_id: UUID
    title: str
    status: CaseStatus
    created_at: datetime
    updated_at: datetime


class CaseWithDocuments(CaseResponse):
    documents: list[DocumentResponse]
