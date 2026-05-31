import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from tests.auth_helpers import auth_headers, auth_user


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_borrower_requires_auth(client):
    response = client.post(
        "/cases/00000000-0000-0000-0000-000000000000/borrowers",
        json={"first_name": "A", "last_name": "B", "role": "primary"},
    )

    assert response.status_code == 401


def test_broker_creates_borrower_for_own_case(client):
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Case A"}, headers=headers).json()

    response = client.post(
        f"/cases/{case['id']}/borrowers",
        json={"first_name": "Alex", "last_name": "Borrower", "role": "primary"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["case_id"] == case["id"]


def test_broker_cannot_create_borrower_for_other_case(client):
    headers_a, _ = auth_user(client)
    headers_b, _ = auth_user(client)
    case_b = client.post("/cases", json={"title": "Case B"}, headers=headers_b).json()

    response = client.post(
        f"/cases/{case_b['id']}/borrowers",
        json={"first_name": "Blocked", "last_name": "Borrower", "role": "primary"},
        headers=headers_a,
    )

    assert response.status_code == 404


def test_manager_can_create_borrower_for_broker_case(client):
    manager = auth_headers(client, "manager")
    _, broker_id = auth_user(client)
    case = client.post(
        "/cases",
        json={"title": "Broker case", "broker_id": broker_id},
        headers=manager,
    ).json()

    response = client.post(
        f"/cases/{case['id']}/borrowers",
        json={"first_name": "Manager", "last_name": "Created", "role": "co_borrower"},
        headers=manager,
    )

    assert response.status_code == 200
    assert response.json()["broker_id"] == broker_id


def test_broker_lists_only_own_case_borrowers(client):
    headers_a, _ = auth_user(client)
    headers_b, _ = auth_user(client)
    case_a = client.post("/cases", json={"title": "A"}, headers=headers_a).json()
    case_b = client.post("/cases", json={"title": "B"}, headers=headers_b).json()
    client.post(
        f"/cases/{case_a['id']}/borrowers",
        json={"first_name": "A", "last_name": "Borrower", "role": "primary"},
        headers=headers_a,
    )
    client.post(
        f"/cases/{case_b['id']}/borrowers",
        json={"first_name": "B", "last_name": "Borrower", "role": "primary"},
        headers=headers_b,
    )

    own_response = client.get(f"/cases/{case_a['id']}/borrowers", headers=headers_a)
    other_response = client.get(f"/cases/{case_b['id']}/borrowers", headers=headers_a)

    assert own_response.status_code == 200
    assert [borrower["first_name"] for borrower in own_response.json()] == ["A"]
    assert other_response.status_code == 404
