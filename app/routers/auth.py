from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import InvalidCredentials, UserAlreadyExists
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserRead
from app.security.jwt import create_access_token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
def register_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    try:
        return auth_service.register_user(db, user_data)
    except UserAlreadyExists as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    try:
        user = auth_service.authenticate_user(db, credentials.email, credentials.password)
    except InvalidCredentials as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    token = create_access_token(UUID(user.id), user.role)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return current_user
