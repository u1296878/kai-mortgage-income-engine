import logging

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.config import settings
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import user_repo
from app.security.passwords import hash_password

logger = logging.getLogger(__name__)


def seed_manager(db: Session) -> None:
    email = settings.manager_email
    password = settings.manager_password
    if not email or not password:
        logger.warning("Manager seed skipped: MANAGER_EMAIL or MANAGER_PASSWORD not configured")
        return
    existing = user_repo.get_first_user_by_role(db, UserRole.manager.value)
    if existing is not None:
        logger.info("Manager account already exists, skipping seed")
        return
    manager = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        role=UserRole.manager.value,
    )
    user_repo.create_user(db, manager)
    logger.info("Manager account created: %s", manager.email)
    log_event("manager_seeded", {"email": manager.email})
