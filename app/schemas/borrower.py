from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.borrower_role import BorrowerRole


class BorrowerCreate(BaseModel):
    first_name: str
    last_name: str
    role: BorrowerRole


class BorrowerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: BorrowerRole | None = None


class BorrowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    broker_id: UUID
    first_name: str
    last_name: str
    role: BorrowerRole
    created_at: datetime
    updated_at: datetime
