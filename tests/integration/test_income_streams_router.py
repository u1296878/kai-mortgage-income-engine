from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.models.result import Result
from tests.auth_helpers import auth_headers, auth_user


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_income_stream_requires_auth(client):
    case_id = uuid4()

    response = client.post(
        f"/cases/{case_id}/income-streams",
        json={"name": "Employment", "stream_type": "employment"},
    )

    assert response.status_code == 401


def test_broker_creates_income_stream_for_own_case(client):
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Case A"}, headers=headers)

    response = client.post(
        f"/cases/{case.json()['id']}/income-streams",
        json={"name": "Employment", "stream_type": "employment"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Employment"
    assert response.json()["case_id"] == case.json()["id"]


def test_broker_cannot_create_income_stream_for_other_case(client):
    headers_a, _ = auth_user(client)
    headers_b, _ = auth_user(client)
    case_b = client.post("/cases", json={"title": "Case B"}, headers=headers_b)

    response = client.post(
        f"/cases/{case_b.json()['id']}/income-streams",
        json={"name": "Blocked", "stream_type": "employment"},
        headers=headers_a,
    )

    assert response.status_code == 404


def test_manager_can_create_income_stream_for_broker_case(client):
    manager = auth_headers(client, "manager")
    broker_headers, broker_id = auth_user(client)
    case = client.post(
        "/cases",
        json={"title": "Broker case", "broker_id": broker_id},
        headers=manager,
    )

    response = client.post(
        f"/cases/{case.json()['id']}/income-streams",
        json={"name": "Manager stream", "stream_type": "other"},
        headers=manager,
    )

    assert response.status_code == 200
    assert response.json()["case_id"] == case.json()["id"]
    assert response.json()["broker_id"] == broker_id


def test_broker_lists_only_own_case_streams(client):
    headers_a, _ = auth_user(client)
    headers_b, _ = auth_user(client)
    case_a = client.post("/cases", json={"title": "A"}, headers=headers_a).json()
    case_b = client.post("/cases", json={"title": "B"}, headers=headers_b).json()
    client.post(
        f"/cases/{case_a['id']}/income-streams",
        json={"name": "A stream", "stream_type": "employment"},
        headers=headers_a,
    )
    client.post(
        f"/cases/{case_b['id']}/income-streams",
        json={"name": "B stream", "stream_type": "employment"},
        headers=headers_b,
    )

    own_response = client.get(f"/cases/{case_a['id']}/income-streams", headers=headers_a)
    other_response = client.get(f"/cases/{case_b['id']}/income-streams", headers=headers_a)

    assert own_response.status_code == 200
    assert [stream["name"] for stream in own_response.json()] == ["A stream"]
    assert other_response.status_code == 404


def test_assign_and_unassign_result_from_income_stream(client, test_db):
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    stream = client.post(
        f"/cases/{case['id']}/income-streams",
        json={"name": "Employment", "stream_type": "employment"},
        headers=headers,
    ).json()
    result = _seed_result(test_db, case["id"], 85000.0, "high")

    assign = client.post(
        f"/income-streams/{stream['id']}/results/{result.id}",
        headers=headers,
    )
    unassign = client.delete(
        f"/income-streams/{stream['id']}/results/{result.id}",
        headers=headers,
    )

    assert assign.status_code == 200
    assert assign.json()["annual_income"] == 85000.0
    assert unassign.status_code == 200
    assert unassign.json()["annual_income"] is None


def test_delete_income_stream_does_not_delete_result(client, test_db):
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    stream = client.post(
        f"/cases/{case['id']}/income-streams",
        json={"name": "Delete me", "stream_type": "employment"},
        headers=headers,
    ).json()
    result = _seed_result(test_db, case["id"], 82000.0, "medium")
    client.post(f"/income-streams/{stream['id']}/results/{result.id}", headers=headers)

    response = client.delete(f"/income-streams/{stream['id']}", headers=headers)

    refreshed = test_db.get(Result, result.id)
    assert response.status_code == 204
    assert refreshed is not None
    assert refreshed.income_stream_id is None


def _seed_result(test_db, case_id, annual_income, confidence):
    document_id = uuid4()
    field = {
        "field": "w2_wages",
        "value": annual_income,
        "document_id": str(document_id),
        "page": 1,
        "bounding_box": {"x1": 1, "y1": 1, "x2": 2, "y2": 2},
    }
    result = Result(
        id=str(uuid4()),
        job_id=str(uuid4()),
        document_id=str(document_id),
        case_id=str(case_id),
        doc_type="w2",
        extracted_fields=[field],
        annual_income=annual_income,
        confidence=confidence,
    )
    test_db.add(result)
    test_db.commit()
    return result
