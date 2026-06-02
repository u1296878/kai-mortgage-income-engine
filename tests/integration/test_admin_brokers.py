import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from tests.auth_helpers import auth_headers


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_manager_lists_brokers(client):
    manager = auth_headers(client, "manager")
    client.post(
        "/auth/register",
        json={"email": "broker@example.com", "password": "secret-password"},
    )

    response = client.get("/admin/brokers", headers=manager)

    assert response.status_code == 200
    assert [broker["email"] for broker in response.json()] == ["broker@example.com"]
    assert response.json()[0]["is_active"] is True


def test_broker_cannot_list_brokers(client):
    broker = auth_headers(client)

    response = client.get("/admin/brokers", headers=broker)

    assert response.status_code == 403


def test_manager_deactivates_broker_and_login_is_rejected(client):
    manager = auth_headers(client, "manager")
    client.post(
        "/auth/register",
        json={"email": "broker@example.com", "password": "secret-password"},
    )
    brokers = client.get("/admin/brokers", headers=manager).json()

    update = client.patch(
        f"/admin/brokers/{brokers[0]['id']}",
        json={"is_active": False},
        headers=manager,
    )
    login = client.post(
        "/auth/login",
        json={"email": "broker@example.com", "password": "secret-password"},
    )

    assert update.status_code == 200
    assert update.json()["is_active"] is False
    assert login.status_code == 401
    assert login.json()["detail"] == "Account is deactivated"


def test_manager_reactivates_broker(client):
    manager = auth_headers(client, "manager")
    client.post(
        "/auth/register",
        json={"email": "broker@example.com", "password": "secret-password"},
    )
    broker_id = client.get("/admin/brokers", headers=manager).json()[0]["id"]
    client.patch(f"/admin/brokers/{broker_id}", json={"is_active": False}, headers=manager)

    response = client.patch(
        f"/admin/brokers/{broker_id}",
        json={"is_active": True},
        headers=manager,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True
