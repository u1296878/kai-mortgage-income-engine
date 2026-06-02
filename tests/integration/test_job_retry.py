import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.models.job_status import JobStatus
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


def test_retry_failed_job_resets_to_pending(client, test_db):
    headers, job_id = _upload_and_get_job(client, test_db)
    job_repo.update_job_status(test_db, job_id, JobStatus.failed.value, "OCR failed")

    response = client.post(f"/jobs/{job_id}/retry", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["error"] is None


def test_retry_complete_job_returns_400(client, test_db):
    headers, job_id = _upload_and_get_job(client, test_db)
    job_repo.update_job_status(test_db, job_id, JobStatus.complete.value)

    response = client.post(f"/jobs/{job_id}/retry", headers=headers)

    assert response.status_code == 400


def _upload_and_get_job(client, test_db):
    headers, _ = auth_user(client)
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2"},
        headers=headers,
    )
    job = job_repo.get_job_by_document(test_db, upload.json()["id"])
    return headers, job.id
