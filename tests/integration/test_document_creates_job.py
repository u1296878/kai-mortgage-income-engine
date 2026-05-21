from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.repositories import job_repo
from app.services import document_service


def test_uploading_document_automatically_creates_pending_job(
    test_db,
    tmp_path,
    monkeypatch,
):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/documents/upload",
        files={"file": ("paystub.pdf", b"contents", "application/pdf")},
        data={"doc_type": "pay_stub"},
    )
    document_id = response.json()["id"]
    job = job_repo.get_job_by_document(test_db, document_id)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert job is not None
    assert job.status == "pending"
