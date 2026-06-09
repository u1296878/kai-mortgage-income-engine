from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.job_status import JobStatus


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    status: JobStatus
    error: str | None
    pages_total: int = 0
    pages_done: int = 0
    current_stage: str | None = None
    percent: float = 0.0
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: JobStatus
    error: str | None
    pages_total: int = 0
    pages_done: int = 0
    current_stage: str | None = None
    percent: float = 0.0
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
