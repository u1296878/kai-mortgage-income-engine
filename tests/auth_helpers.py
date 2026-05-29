from uuid import uuid4

from fastapi.testclient import TestClient


def auth_headers(client: TestClient, role: str = "broker") -> dict[str, str]:
    password = "secret-password"
    email = f"{role}-{uuid4()}@example.com"
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def auth_user(client: TestClient, role: str = "broker") -> tuple[dict[str, str], str]:
    headers = auth_headers(client, role)
    response = client.get("/auth/me", headers=headers)
    return headers, response.json()["id"]
