from uuid import uuid4

import pytest

from app.exceptions import Unauthorized
from app.security.jwt import create_access_token, decode_access_token


def test_create_access_token_can_be_decoded():
    user_id = uuid4()

    token = create_access_token(user_id, "broker")
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "broker"


def test_decode_access_token_rejects_invalid_token():
    with pytest.raises(Unauthorized):
        decode_access_token("not-a-valid-token")
