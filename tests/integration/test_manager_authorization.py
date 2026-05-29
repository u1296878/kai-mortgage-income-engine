import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.models.result import Result
from app.repositories import job_repo
from app.storage import local_storage
from tests.auth_helpers import auth_headers, auth_user


@pytest.fixture
def client(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_manager_can_create_filter_and_access_broker_records(client, test_db):
    manager_headers = auth_headers(client, "manager")
    broker_a_headers, broker_a_id = auth_user(client)
    _, broker_b_id = auth_user(client)
    case_a = _create_case(client, manager_headers, broker_a_id, "A case")
    case_b = _create_case(client, manager_headers, broker_b_id, "B case")
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2"},
        headers=broker_a_headers,
    )
    document_id = upload.json()["id"]
    job = job_repo.get_job_by_document(test_db, document_id)
    test_db.add(_result(job.id, document_id, case_a["id"]))
    test_db.commit()

    all_cases = client.get("/cases", headers=manager_headers)
    filtered = client.get(
        "/cases",
        params={"broker_id": broker_b_id},
        headers=manager_headers,
    )
    document_response = client.get(f"/documents/{document_id}", headers=manager_headers)
    job_response = client.get(f"/jobs/{job.id}", headers=manager_headers)
    result_response = client.get(f"/jobs/{job.id}/result", headers=manager_headers)

    assert client.get(f"/cases/{case_a['id']}", headers=manager_headers).status_code == 200
    assert client.get(f"/cases/{case_b['id']}", headers=manager_headers).status_code == 200
    assert {case["id"] for case in all_cases.json()} == {case_a["id"], case_b["id"]}
    assert [case["id"] for case in filtered.json()] == [case_b["id"]]
    assert document_response.status_code == 200
    assert job_response.status_code == 200
    assert result_response.status_code == 200


def _create_case(client, headers, broker_id, title):
    response = client.post(
        "/cases",
        json={"title": title, "broker_id": broker_id},
        headers=headers,
    )
    return response.json()


def _result(job_id, document_id, case_id) -> Result:
    field = {
        "field": "w2_wages",
        "value": 85000.0,
        "document_id": str(document_id),
        "page": 1,
        "bounding_box": {"x1": 1, "y1": 1, "x2": 2, "y2": 2},
    }
    return Result(
        job_id=str(job_id),
        document_id=str(document_id),
        case_id=str(case_id),
        doc_type="w2",
        extracted_fields=[field],
        annual_income=85000.0,
        confidence="high",
    )
