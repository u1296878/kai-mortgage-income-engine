import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from tests.auth_helpers import auth_user


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_assign_stream_to_borrower(client):
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    borrower = client.post(
        f"/cases/{case['id']}/borrowers",
        json={"first_name": "Alex", "last_name": "Smith", "role": "primary"},
        headers=headers,
    ).json()
    stream = client.post(
        f"/cases/{case['id']}/income-streams",
        json={"name": "Employment", "stream_type": "employment"},
        headers=headers,
    ).json()

    response = client.post(
        f"/borrowers/{borrower['id']}/income-streams/{stream['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["borrower_id"] == borrower["id"]


def test_unassign_stream_from_borrower(client):
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    borrower = client.post(
        f"/cases/{case['id']}/borrowers",
        json={"first_name": "Alex", "last_name": "Smith", "role": "primary"},
        headers=headers,
    ).json()
    stream = client.post(
        f"/cases/{case['id']}/income-streams",
        json={"name": "Employment", "stream_type": "employment"},
        headers=headers,
    ).json()
    client.post(
        f"/borrowers/{borrower['id']}/income-streams/{stream['id']}",
        headers=headers,
    )

    response = client.delete(
        f"/borrowers/{borrower['id']}/income-streams/{stream['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["borrower_id"] is None


def test_delete_borrower_does_not_delete_stream(client):
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    borrower = client.post(
        f"/cases/{case['id']}/borrowers",
        json={"first_name": "Alex", "last_name": "Smith", "role": "primary"},
        headers=headers,
    ).json()
    stream = client.post(
        f"/cases/{case['id']}/income-streams",
        json={"name": "Employment", "stream_type": "employment"},
        headers=headers,
    ).json()
    client.post(
        f"/borrowers/{borrower['id']}/income-streams/{stream['id']}",
        headers=headers,
    )

    delete_response = client.delete(f"/borrowers/{borrower['id']}", headers=headers)
    stream_response = client.get(f"/income-streams/{stream['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert stream_response.status_code == 200
    assert stream_response.json()["borrower_id"] is None


def test_broker_cannot_assign_other_broker_stream(client):
    headers_a, _ = auth_user(client)
    headers_b, _ = auth_user(client)
    case_a = client.post("/cases", json={"title": "A"}, headers=headers_a).json()
    case_b = client.post("/cases", json={"title": "B"}, headers=headers_b).json()
    borrower = client.post(
        f"/cases/{case_a['id']}/borrowers",
        json={"first_name": "A", "last_name": "Borrower", "role": "primary"},
        headers=headers_a,
    ).json()
    stream_b = client.post(
        f"/cases/{case_b['id']}/income-streams",
        json={"name": "B stream", "stream_type": "employment"},
        headers=headers_b,
    ).json()

    response = client.post(
        f"/borrowers/{borrower['id']}/income-streams/{stream_b['id']}",
        headers=headers_a,
    )

    assert response.status_code == 404
