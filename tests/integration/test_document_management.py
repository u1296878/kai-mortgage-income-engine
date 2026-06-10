import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.exceptions import DocumentNotFound
from app.main import app
from app.models.result import Result
from app.repositories import document_repo, job_repo, result_repo
from app.storage import local_storage
from tests.local_user_helpers import local_user


@pytest.fixture
def client(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_delete_document_removes_record_file_job_and_result(client, test_db, tmp_path):
    headers, _ = local_user(client)
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2"},
        headers=headers,
    )
    document_id = upload.json()["id"]
    job = job_repo.get_job_by_document(test_db, document_id)
    test_db.add(_result(job.id, document_id))
    test_db.commit()

    response = client.delete(f"/documents/{document_id}", headers=headers)

    assert response.status_code == 204
    assert not (tmp_path / document_id / "document").exists()
    assert job_repo.get_job_by_document(test_db, document_id) is None
    assert result_repo.get_result_by_job(test_db, job.id) is None
    with pytest.raises(DocumentNotFound):
        document_repo.get_document(test_db, document_id)


def test_remove_document_from_case_clears_document_case(client, test_db):
    headers, broker_id = local_user(client)
    case = client.post(
        "/cases",
        json={"title": "Borrower Case", "broker_id": broker_id},
        headers=headers,
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2", "case_id": case.json()["id"]},
        headers=headers,
    )

    response = client.delete(f"/documents/{upload.json()['id']}/case", headers=headers)

    assert response.status_code == 200
    assert response.json()["case_id"] is None


def _result(job_id, document_id) -> Result:
    return Result(
        job_id=str(job_id),
        document_id=str(document_id),
        doc_type="w2",
        extracted_fields=[],
        annual_income=85000.0,
        confidence="high",
    )
