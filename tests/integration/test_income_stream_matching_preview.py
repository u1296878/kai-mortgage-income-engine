from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from tests.auth_helpers import auth_headers, auth_user
from tests.income_stream_match_helpers import seed_result, w2_fields


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_case_match_preview_requires_auth(client):
    case_id = uuid4()

    response = client.get(f"/cases/{case_id}/income-stream-matches")

    assert response.status_code == 401


def test_broker_can_preview_matches_for_own_case(client, test_db):
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Own"}, headers=headers).json()
    seed_result(test_db, case["id"], "w2", w2_fields("Acme Corp"))

    response = client.get(f"/cases/{case['id']}/income-stream-matches", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "reason" in response.json()[0]


def test_broker_cannot_preview_matches_for_other_case(client, test_db):
    headers_a, _ = auth_user(client)
    headers_b, _ = auth_user(client)
    case_b = client.post("/cases", json={"title": "Other"}, headers=headers_b).json()
    seed_result(test_db, case_b["id"], "w2", w2_fields("Acme Corp"))

    response = client.get(f"/cases/{case_b['id']}/income-stream-matches", headers=headers_a)

    assert response.status_code == 404


def test_manager_can_preview_matches_for_any_case(client, test_db):
    manager = auth_headers(client, "manager")
    _, broker_id = auth_user(client)
    case = client.post(
        "/cases",
        json={"title": "Broker case", "broker_id": broker_id},
        headers=manager,
    ).json()
    seed_result(test_db, case["id"], "w2", w2_fields("Acme Corp"))

    response = client.get(f"/cases/{case['id']}/income-stream-matches", headers=manager)

    assert response.status_code == 200
    assert response.json()[0]["confidence"] in {"high", "medium", "low"}
