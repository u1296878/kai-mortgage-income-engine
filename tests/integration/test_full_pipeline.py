from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.exceptions import ExtractionFailed
from app.main import app
from app.repositories import job_repo, result_repo
from app.services import document_service, extraction_service
from app.workers.job_worker import process_next_job


def test_full_pipeline_upload_to_result(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"doc_type": "w2"},
    )
    document_id = response.json()["id"]
    job = job_repo.get_job_by_document(test_db, document_id)
    original_status = job.status
    processed = process_next_job(test_db)
    updated_job = job_repo.get_job(test_db, job.id)
    result = result_repo.get_result_by_job(test_db, job.id)

    app.dependency_overrides.clear()
    assert original_status == "pending"
    assert processed is True
    assert updated_job.status == "complete"
    assert result.annual_income is not None
    assert result.extracted_fields[0]["document_id"] == document_id
    assert result.extracted_fields[0]["page"] == 1
    assert "bounding_box" in result.extracted_fields[0]


def test_full_pipeline_failed_extraction_marks_job_failed(
    test_db,
    tmp_path,
    monkeypatch,
):
    def override_db():
        yield test_db

    def raise_extraction_failed(document_id, file_path, doc_type):
        raise ExtractionFailed("extractor failed")

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    monkeypatch.setattr(extraction_service, "extract_fields", raise_extraction_failed)
    client = TestClient(app)

    response = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"doc_type": "w2"},
    )
    document_id = response.json()["id"]
    job = job_repo.get_job_by_document(test_db, document_id)
    process_next_job(test_db)
    updated_job = job_repo.get_job(test_db, job.id)
    result = result_repo.get_result_by_job(test_db, job.id)

    app.dependency_overrides.clear()
    assert updated_job.status == "failed"
    assert updated_job.error == "extractor failed"
    assert result is None
