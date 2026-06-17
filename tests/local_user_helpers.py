def local_headers(*_args, **_kwargs) -> dict[str, str]:
    return {}


def make_user(user_id=None, role: str = "local"):
    class LocalTestUser:
        def __init__(self) -> None:
            self.id = str(user_id) if user_id else "local"
            self.email = "local@example.com"
            self.role = role

        def __str__(self) -> str:
            return self.id

    return LocalTestUser()
