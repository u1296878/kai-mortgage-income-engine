from uuid import uuid4

from app.exceptions import ExtractionFailed
from app.models.document import Document
from app.models.job import Job
from app.repositories import job_repo, result_repo
from app.services import extraction_service, job_processing_service


def make_document(doc_type="other"):
    return Document(
        id=str(uuid4()),
        filename="other.pdf",
        doc_type=doc_type,
        storage_path="storage/path/other.pdf",
    )


def make_pending_job(document_id):
    return Job(id=str(uuid4()), document_id=str(document_id), status="pending")


def test_process_next_job_returns_false_when_queue_empty(test_db):
    processed = job_processing_service.process_next_job(test_db)

    assert processed is False


def test_process_next_job_claims_and_processes_job(test_db):
    document = make_document()
    job = make_pending_job(document.id)
    test_db.add_all([document, job])
    test_db.commit()

    processed = job_processing_service.process_next_job(test_db)
    result = result_repo.get_result_by_job(test_db, job.id)
    updated_job = job_repo.get_job(test_db, job.id)

    assert processed is True
    assert result is not None
    assert updated_job.status == "complete"


def test_process_next_job_marks_job_failed_on_extraction_error(test_db, monkeypatch):
    document = make_document()
    job = make_pending_job(document.id)
    test_db.add_all([document, job])
    test_db.commit()

    def raise_extraction_failed(document_id, file_path, doc_type):
        raise ExtractionFailed("extraction exploded")

    monkeypatch.setattr(extraction_service, "extract_fields", raise_extraction_failed)
    job_processing_service.process_next_job(test_db)
    updated_job = job_repo.get_job(test_db, job.id)

    assert updated_job.status == "failed"
    assert updated_job.error == "extraction exploded"
