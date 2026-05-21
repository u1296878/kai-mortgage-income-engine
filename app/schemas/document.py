from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document_type import DocumentType


class DocumentUpload(BaseModel):
    doc_type: DocumentType


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    doc_type: DocumentType
    case_id: UUID | None
    uploaded_at: datetime


class DocumentCaseLink(BaseModel):
    case_id: UUID
