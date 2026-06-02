from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions import Unauthorized, UserNotFound
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import user_repo


def list_brokers(db: Session, current_user: User) -> list[User]:
    _ensure_manager(current_user)
    return user_repo.list_users_by_role(db, UserRole.broker.value)


def update_broker_status(
    db: Session,
    broker_id: UUID,
    is_active: bool,
    current_user: User,
) -> User:
    _ensure_manager(current_user)
    broker = user_repo.get_user_by_id(db, broker_id)
    if broker is None or broker.role != UserRole.broker.value:
        raise UserNotFound(f"Broker not found: {broker_id}")
    updated = user_repo.update_user_active(db, broker_id, is_active)
    if updated is None:
        raise UserNotFound(f"Broker not found: {broker_id}")
    return updated


def _ensure_manager(user: User) -> None:
    if user.role != UserRole.manager.value:
        raise Unauthorized("Manager access required")
