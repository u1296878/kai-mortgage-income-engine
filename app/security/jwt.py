from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.config import settings
from app.exceptions import Unauthorized


def create_access_token(user_id: UUID, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes,
    )
    payload = {"sub": str(user_id), "role": role, "exp": int(expires_at.timestamp())}
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as error:
        raise Unauthorized("Access token expired")
    except (InvalidTokenError, ValueError) as error:
        raise Unauthorized("Invalid access token") from error
    return payload
