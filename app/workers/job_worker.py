from pathlib import Path
from threading import Event
from time import sleep
from uuid import UUID

from sqlalchemy.orm import sessionmaker

from app.audit.logger import log_event
from app.models.job_status import JobStatus
from app.repositories import document_repo, job_repo
from app.services import extraction_service, result_service


def run_worker(
    db_factory: sessionmaker,
    poll_interval_seconds: int = 5,
    stop_event: Event | None = None,
) -> None:
    worker_stop_event = stop_event or Event()
    log_event("worker_started", {"poll_interval_seconds": poll_interval_seconds})
    _worker_loop(db_factory, poll_interval_seconds, worker_stop_event)


def process_next_job(db) -> bool:
    job = None
    try:
        job = job_repo.claim_next_pending_job(db)
        if job is None:
            return False
        document = document_repo.get_document(db, UUID(job.document_id))
        fields = extraction_service.extract_fields(
            UUID(document.id),
            Path(document.storage_path),
            document.doc_type,
        )
        result = result_service.save_extraction_result(
            db,
            UUID(job.id),
            UUID(document.id),
            UUID(document.case_id) if document.case_id else None,
            document.doc_type,
            fields,
        )
        job_repo.update_job_status(db, UUID(job.id), JobStatus.complete.value)
        log_event(
            "job_completed",
            {"job_id": job.id, "document_id": document.id, "result_id": result.id},
        )
        return True
    except Exception as error:
        if job is not None:
            job_repo.update_job_status(
                db,
                UUID(job.id),
                JobStatus.failed.value,
                str(error),
            )
            log_event("job_failed", {"job_id": job.id, "error": str(error)})
        else:
            log_event("job_failed", {"job_id": None, "error": str(error)})
        return False


def _worker_loop(
    db_factory: sessionmaker,
    poll_interval_seconds: int,
    stop_event: Event,
) -> None:
    while not stop_event.is_set():
        db = db_factory()
        try:
            process_next_job(db)
        except Exception as error:
            log_event("worker_error", {"error": str(error)})
        finally:
            db.close()
        if stop_event.wait(poll_interval_seconds):
            break
