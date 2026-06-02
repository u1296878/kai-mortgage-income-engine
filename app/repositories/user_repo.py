from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def create_user(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.scalars(statement).first()


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, str(user_id))


def get_first_user_by_role(db: Session, role: str) -> User | None:
    statement = select(User).where(User.role == role).limit(1)
    return db.scalars(statement).first()


def list_users_by_role(db: Session, role: str) -> list[User]:
    statement = select(User).where(User.role == role).order_by(User.created_at, User.email)
    return list(db.scalars(statement).all())


def update_user_active(db: Session, user_id: UUID, is_active: bool) -> User | None:
    user = get_user_by_id(db, user_id)
    if user is None:
        return None
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
