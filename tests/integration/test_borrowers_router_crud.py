import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from tests.local_user_helpers import local_headers, local_user


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_broker_creates_borrower_for_own_case(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case A"}, headers=headers).json()

    response = client.post(
        f"/cases/{case['id']}/borrowers",
        json={"first_name": "Alex", "last_name": "Borrower", "role": "primary"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["case_id"] == case["id"]
