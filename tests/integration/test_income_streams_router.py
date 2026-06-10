from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.models.result import Result
from tests.local_user_helpers import local_headers, local_user


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_broker_creates_income_stream_for_own_case(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case A"}, headers=headers)

    response = client.post(
        f"/cases/{case.json()['id']}/income-streams",
        json={"name": "Employment", "stream_type": "employment"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Employment"
    assert response.json()["case_id"] == case.json()["id"]


def test_assign_and_unassign_result_from_income_stream(client, test_db):
    headers, _ = local_user(client)
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
    headers, _ = local_user(client)
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
