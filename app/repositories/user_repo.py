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
