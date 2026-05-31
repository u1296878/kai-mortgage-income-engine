from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.repositories import job_repo
from app.storage import local_storage
from tests.auth_helpers import auth_headers, auth_user


def test_uploading_document_automatically_creates_pending_job(
    test_db,
    tmp_path,
    monkeypatch,
):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    client = TestClient(app)
    headers = auth_headers(client)

    response = client.post(
        "/documents/upload",
        files={"file": ("paystub.pdf", b"contents", "application/pdf")},
        data={"doc_type": "pay_stub"},
        headers=headers,
    )
    document_id = response.json()["id"]
    job = job_repo.get_job_by_document(test_db, document_id)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert job is not None
    assert job.status == "pending"


def test_upload_with_case_id_sets_case_before_job_creation(
    test_db,
    tmp_path,
    monkeypatch,
):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    client = TestClient(app)
    headers, broker_id = auth_user(client)
    case_response = client.post(
        "/cases",
        json={"title": "Upload Flow Case", "broker_id": broker_id},
        headers=headers,
    )
    case_id = case_response.json()["id"]

    response = client.post(
        "/documents/upload",
        files={"file": ("paystub.pdf", b"contents", "application/pdf")},
        data={"doc_type": "pay_stub", "case_id": case_id},
        headers=headers,
    )
    document_id = response.json()["id"]
    job = job_repo.get_job_by_document(test_db, document_id)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["case_id"] == case_id
    assert job is not None
    assert job.status == "pending"
