from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.exceptions import Unauthorized
from app.models.user import User
from app.repositories import user_repo
from app.security.jwt import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        user = user_repo.get_user_by_id(db, UUID(payload["sub"]))
    except (KeyError, ValueError, Unauthorized) as error:
        raise HTTPException(status_code=401, detail="Invalid credentials") from error
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user
