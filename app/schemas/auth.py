from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.user_role import UserRole


class UserCreate(BaseModel):
    email: str
    password: str
    role: UserRole = UserRole.broker


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
