from uuid import uuid4

from app.runtime.local_user import LOCAL_USER_ID


def local_headers(*_args, **_kwargs) -> dict[str, str]:
    return {}


def local_user(*_args, **_kwargs) -> tuple[dict[str, str], str]:
    return {}, str(LOCAL_USER_ID)


def make_user(user_id=None, role: str = "local"):
    class LocalTestUser:
        def __init__(self) -> None:
            self.id = str(user_id or uuid4())
            self.email = "local@example.com"
            self.role = role

        def __str__(self) -> str:
            return self.id

    return LocalTestUser()
