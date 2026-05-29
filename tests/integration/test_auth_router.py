from fastapi.testclient import TestClient
import pytest

from app.dependencies import get_db
from app.main import app


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_register_user_returns_user_without_password(client):

    response = client.post(
        "/auth/register",
        json={"email": "broker@example.com", "password": "secret-password"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "broker@example.com"
    assert response.json()["role"] == "broker"
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()


def test_register_duplicate_email_returns_error(client):
    payload = {"email": "broker@example.com", "password": "secret-password"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409


def test_login_returns_bearer_token(client):
    payload = {"email": "broker@example.com", "password": "secret-password"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={"email": "broker@example.com", "password": "secret-password"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "broker@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_auth_me_returns_current_user_with_valid_token(client):
    payload = {"email": "manager@example.com", "password": "secret-password", "role": "manager"}
    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "manager@example.com"
    assert response.json()["role"] == "manager"


def test_auth_me_without_token_returns_401(client):

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_auth_me_with_invalid_token_returns_401(client):

    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
