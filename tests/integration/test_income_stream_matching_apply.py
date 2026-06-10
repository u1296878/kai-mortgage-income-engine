from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.models.income_stream import IncomeStream
from app.models.result import Result
from tests.local_user_helpers import local_headers, local_user
from tests.income_stream_match_helpers import seed_result, w2_fields


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_high_confidence_matches_can_be_applied(client, test_db):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Apply"}, headers=headers).json()
    stream = IncomeStream(
        case_id=case["id"],
        broker_id=case["broker_id"],
        name="Employment: Acme Corp",
        stream_type="employment",
    )
    result = seed_result(test_db, case["id"], "w2", w2_fields("Acme Corp"))
    test_db.add(stream)
    test_db.commit()

    response = client.post(
        f"/cases/{case['id']}/income-stream-matches/apply",
        json={},
        headers=headers,
    )

    refreshed = test_db.get(Result, result.id)
    assert response.status_code == 200
    assert response.json()["applied_count"] == 1
    assert refreshed.income_stream_id == stream.id


def test_apply_matches_does_not_cross_case_boundaries(client, test_db):
    headers = local_headers(client)
    case_a = client.post(
        "/cases",
        json={"title": "Case A", "broker_id": str(uuid4())},
        headers=headers,
    ).json()
    case_b = client.post(
        "/cases",
        json={"title": "Case B", "broker_id": str(uuid4())},
        headers=headers,
    ).json()
    stream_b = IncomeStream(
        case_id=case_b["id"],
        broker_id=case_b["broker_id"],
        name="Employment: Acme Corp",
        stream_type="employment",
    )
    result_a = seed_result(test_db, case_a["id"], "w2", w2_fields("Acme Corp"))
    test_db.add(stream_b)
    test_db.commit()

    response = client.post(
        f"/cases/{case_a['id']}/income-stream-matches/apply",
        json={},
        headers=headers,
    )

    refreshed = test_db.get(Result, result_a.id)
    assert response.status_code == 200
    assert refreshed.income_stream_id != stream_b.id


def test_manual_assignment_is_preserved_when_matching_runs(client, test_db):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Manual"}, headers=headers).json()
    stream = IncomeStream(
        case_id=case["id"],
        broker_id=case["broker_id"],
        name="Employment: Acme Corp",
        stream_type="employment",
    )
    test_db.add(stream)
    test_db.commit()
    result = seed_result(test_db, case["id"], "w2", w2_fields("Acme Corp"), stream.id)

    response = client.post(
        f"/cases/{case['id']}/income-stream-matches/apply",
        json={},
        headers=headers,
    )

    refreshed = test_db.get(Result, result.id)
    assert response.status_code == 200
    assert response.json()["applied_count"] == 0
    assert refreshed.income_stream_id == stream.id
