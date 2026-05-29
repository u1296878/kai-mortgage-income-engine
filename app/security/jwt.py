import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.config import settings
from app.exceptions import Unauthorized


def create_access_token(user_id: UUID, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes,
    )
    payload = {"sub": str(user_id), "role": role, "exp": int(expires_at.timestamp())}
    return _encode(payload)


def decode_access_token(token: str) -> dict:
    try:
        header_text, payload_text, signature = token.split(".")
        expected = _sign(f"{header_text}.{payload_text}")
        payload = json.loads(_decode_part(payload_text))
    except (ValueError, json.JSONDecodeError) as error:
        raise Unauthorized("Invalid access token") from error
    if not hmac.compare_digest(signature, expected):
        raise Unauthorized("Invalid access token")
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise Unauthorized("Access token expired")
    return payload


def _encode(payload: dict) -> str:
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    header_text = _encode_part(header)
    payload_text = _encode_part(payload)
    signature = _sign(f"{header_text}.{payload_text}")
    return f"{header_text}.{payload_text}.{signature}"


def _encode_part(data: dict) -> str:
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _decode_part(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}").decode("utf-8")


def _sign(message: str) -> str:
    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
