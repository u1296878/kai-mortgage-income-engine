import pytest

from app.exceptions import InvalidCredentials, UserAlreadyExists
from app.models.user_role import UserRole
from app.repositories import user_repo
from app.schemas.auth import UserCreate
from app.security.passwords import verify_password
from app.services import auth_service


def make_user(email="broker@example.com", password="secret-password"):
    return UserCreate(email=email, password=password, role=UserRole.broker)


def test_register_user_hashes_password(test_db):
    user_data = make_user()

    user = auth_service.register_user(test_db, user_data)

    assert user.hashed_password != user_data.password
    assert verify_password(user_data.password, user.hashed_password)


def test_register_user_rejects_duplicate_email(test_db):
    user_data = make_user()
    auth_service.register_user(test_db, user_data)

    with pytest.raises(UserAlreadyExists):
        auth_service.register_user(test_db, user_data)


def test_authenticate_user_accepts_valid_credentials(test_db):
    user_data = make_user()
    auth_service.register_user(test_db, user_data)

    user = auth_service.authenticate_user(test_db, user_data.email, user_data.password)

    assert user.email == user_data.email


def test_authenticate_user_rejects_invalid_password(test_db):
    user_data = make_user()
    auth_service.register_user(test_db, user_data)

    with pytest.raises(InvalidCredentials):
        auth_service.authenticate_user(test_db, user_data.email, "wrong-password")


def test_user_repo_get_user_by_id_returns_user(test_db):
    user = auth_service.register_user(test_db, make_user())

    found = user_repo.get_user_by_id(test_db, user.id)

    assert found.email == user.email
