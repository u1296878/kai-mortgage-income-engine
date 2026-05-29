import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.models.result import Result
from app.repositories import job_repo
from app.storage import local_storage
from tests.auth_helpers import auth_user


@pytest.fixture
def client(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_broker_lists_only_their_own_cases(client):
    broker_a_headers, broker_a_id = auth_user(client)
    broker_b_headers, broker_b_id = auth_user(client)
    client.post("/cases", json={"title": "A case"}, headers=broker_a_headers)
    client.post("/cases", json={"title": "B case"}, headers=broker_b_headers)

    response = client.get(
        "/cases",
        params={"broker_id": broker_b_id},
        headers=broker_a_headers,
    )

    assert response.status_code == 200
    assert [case["broker_id"] for case in response.json()] == [broker_a_id]


def test_broker_cannot_read_update_or_delete_another_broker_case(client):
    broker_a_headers, _ = auth_user(client)
    broker_b_headers, _ = auth_user(client)
    created = client.post(
        "/cases",
        json={"title": "Broker B case"},
        headers=broker_b_headers,
    )
    case_id = created.json()["id"]

    get_response = client.get(f"/cases/{case_id}", headers=broker_a_headers)
    patch_response = client.patch(
        f"/cases/{case_id}",
        json={"title": "Nope"},
        headers=broker_a_headers,
    )
    delete_response = client.delete(f"/cases/{case_id}", headers=broker_a_headers)

    assert get_response.status_code == 404
    assert patch_response.status_code == 404
    assert delete_response.status_code == 404


def test_broker_cannot_access_another_brokers_document_job_or_result(client, test_db):
    broker_a_headers, _ = auth_user(client)
    broker_b_headers, _ = auth_user(client)
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2"},
        headers=broker_b_headers,
    )
    document_id = upload.json()["id"]
    job = job_repo.get_job_by_document(test_db, document_id)
    test_db.add(_result(job.id, document_id))
    test_db.commit()

    document_response = client.get(f"/documents/{document_id}", headers=broker_a_headers)
    job_response = client.get(f"/jobs/{job.id}", headers=broker_a_headers)
    result_response = client.get(f"/jobs/{job.id}/result", headers=broker_a_headers)

    assert document_response.status_code == 404
    assert job_response.status_code == 404
    assert result_response.status_code == 404


def test_broker_cannot_link_document_to_another_broker_case(client):
    broker_a_headers, _ = auth_user(client)
    broker_b_headers, _ = auth_user(client)
    broker_a_document = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2"},
        headers=broker_a_headers,
    )
    broker_b_document = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2"},
        headers=broker_b_headers,
    )
    broker_a_case = client.post(
        "/cases",
        json={"title": "Broker A case"},
        headers=broker_a_headers,
    )
    broker_b_case = client.post(
        "/cases",
        json={"title": "Broker B case"},
        headers=broker_b_headers,
    )

    own_doc_to_other_case = client.patch(
        f"/documents/{broker_a_document.json()['id']}/case",
        json={"case_id": broker_b_case.json()["id"]},
        headers=broker_a_headers,
    )
    other_doc_to_own_case = client.patch(
        f"/documents/{broker_b_document.json()['id']}/case",
        json={"case_id": broker_a_case.json()["id"]},
        headers=broker_a_headers,
    )

    assert own_doc_to_other_case.status_code == 404
    assert other_doc_to_own_case.status_code == 404


def test_broker_cannot_access_another_broker_case_summary(client, test_db):
    broker_a_headers, _ = auth_user(client)
    broker_b_headers, _ = auth_user(client)
    case = client.post(
        "/cases",
        json={"title": "Broker B case"},
        headers=broker_b_headers,
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2"},
        headers=broker_b_headers,
    )
    job = job_repo.get_job_by_document(test_db, upload.json()["id"])
    test_db.add(_result(job.id, upload.json()["id"], case.json()["id"]))
    test_db.commit()

    response = client.get(
        f"/cases/{case.json()['id']}/summary",
        headers=broker_a_headers,
    )

    assert response.status_code == 404


def _result(job_id, document_id, case_id=None) -> Result:
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
        case_id=str(case_id) if case_id else None,
        doc_type="w2",
        extracted_fields=[field],
        annual_income=85000.0,
        confidence="high",
    )
