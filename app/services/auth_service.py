from sqlalchemy.orm import Session

from app.exceptions import AccountDeactivated, InvalidCredentials, UserAlreadyExists
from app.models.user import User
from app.repositories import user_repo
from app.schemas.auth import UserCreate
from app.security.passwords import hash_password, verify_password


def register_user(db: Session, user_data: UserCreate) -> User:
    email = user_data.email.lower()
    if user_repo.get_user_by_email(db, email) is not None:
        raise UserAlreadyExists(f"User already exists: {email}")
    user = User(
        email=email,
        hashed_password=hash_password(user_data.password),
        role="broker",
    )
    return user_repo.create_user(db, user)


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = user_repo.get_user_by_email(db, email.lower())
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentials("Invalid email or password")
    if not user.is_active:
        raise AccountDeactivated("Account is deactivated")
    return user
