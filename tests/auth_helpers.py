from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.models.user import User
from app.security.passwords import hash_password


def auth_headers(client: TestClient, role: str = "broker") -> dict[str, str]:
    password = "secret-password"
    email = f"{role}-{uuid4()}@example.com"
    if role == "manager":
        _create_user_directly(email, password, role)
    else:
        client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def auth_user(client: TestClient, role: str = "broker") -> tuple[dict[str, str], str]:
    headers = auth_headers(client, role)
    response = client.get("/auth/me", headers=headers)
    return headers, response.json()["id"]


def _create_user_directly(email: str, password: str, role: str) -> None:
    override = app.dependency_overrides.get(get_db)
    if override is None:
        raise RuntimeError("Manager test users require a test database override")
    db = next(override())
    db.add(
        User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
        )
    )
    db.commit()
