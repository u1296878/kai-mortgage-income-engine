from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

RoleValue = Literal["primary", "co_borrower"]


class BorrowerCreate(BaseModel):
    first_name: str
    last_name: str
    role: RoleValue


class BorrowerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: RoleValue | None = None


class BorrowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    broker_id: UUID
    first_name: str
    last_name: str
    role: RoleValue
    created_at: datetime
    updated_at: datetime
