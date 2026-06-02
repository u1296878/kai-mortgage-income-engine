from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import Unauthorized, UserNotFound
from app.models.user import User
from app.schemas.admin import BrokerStatusUpdate
from app.schemas.auth import UserRead
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/brokers", response_model=list[UserRead])
def list_brokers(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[UserRead]:
    try:
        return admin_service.list_brokers(db, current_user)
    except Unauthorized as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.patch("/brokers/{broker_id}", response_model=UserRead)
def update_broker_status(
    broker_id: UUID,
    payload: BrokerStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    try:
        return admin_service.update_broker_status(
            db,
            broker_id,
            payload.is_active,
            current_user,
        )
    except Unauthorized as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except UserNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
