from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from tests.local_user_helpers import local_headers, local_user
from tests.income_stream_match_helpers import seed_result, w2_fields


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_local_user_can_preview_matches_for_case(client, test_db):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Own"}, headers=headers).json()
    seed_result(test_db, case["id"], "w2", w2_fields("Acme Corp"))

    response = client.get(f"/cases/{case['id']}/income-stream-matches", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "reason" in response.json()[0]


def test_local_user_can_preview_matches_for_case_with_legacy_broker_id(client, test_db):
    headers = local_headers(client)
    _, broker_id = local_user(client)
    case = client.post(
        "/cases",
        json={"title": "Broker case", "broker_id": broker_id},
        headers=headers,
    ).json()
    seed_result(test_db, case["id"], "w2", w2_fields("Acme Corp"))

    response = client.get(f"/cases/{case['id']}/income-stream-matches", headers=headers)

    assert response.status_code == 200
    assert response.json()[0]["confidence"] in {"high", "medium", "low"}
