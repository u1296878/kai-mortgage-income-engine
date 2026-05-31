import logging

from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import user_repo
from app.seed import seed_manager
from app.security.passwords import verify_password


def test_seed_creates_manager_when_none_exists(test_db, monkeypatch):
    monkeypatch.setattr(settings, "manager_email", "manager@example.com")
    monkeypatch.setattr(settings, "manager_password", "secret-password")

    seed_manager(test_db)

    manager = user_repo.get_first_user_by_role(test_db, UserRole.manager.value)
    assert manager is not None
    assert manager.email == "manager@example.com"
    assert verify_password("secret-password", manager.hashed_password)


def test_seed_skips_when_manager_exists(test_db, monkeypatch, caplog):
    monkeypatch.setattr(settings, "manager_email", "manager@example.com")
    monkeypatch.setattr(settings, "manager_password", "secret-password")
    seed_manager(test_db)
    caplog.set_level(logging.INFO)

    seed_manager(test_db)

    managers = list(
        test_db.scalars(
            select(User).where(User.role == UserRole.manager.value),
        ).all(),
    )
    assert len(managers) == 1
    assert "Manager account already exists, skipping seed" in caplog.text


def test_seed_skips_when_no_credentials_configured(test_db, monkeypatch, caplog):
    monkeypatch.setattr(settings, "manager_email", None)
    monkeypatch.setattr(settings, "manager_password", None)
    caplog.set_level(logging.WARNING)

    seed_manager(test_db)

    manager = user_repo.get_first_user_by_role(test_db, UserRole.manager.value)
    assert manager is None
    assert "Manager seed skipped: MANAGER_EMAIL or MANAGER_PASSWORD not configured" in caplog.text
