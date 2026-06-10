from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import DocumentNotFound, JobAlreadyProcessed, JobNotFound
from app.models.job import Job
from app.models.job_status import JobStatus
from app.repositories import document_repo, job_repo


def create_job_for_document(db: Session, document_id: UUID) -> Job:
    job = Job(document_id=str(document_id))
    saved_job = job_repo.create_job(db, job)
    log_event(
        "job_created",
        {"job_id": saved_job.id, "document_id": saved_job.document_id},
    )
    return saved_job


def get_job_status(db: Session, job_id: UUID, local_user_id: UUID) -> Job:
    job = job_repo.get_job(db, job_id)
    _ensure_job_document_access(db, job, local_user_id)
    return job


def get_job_for_document(
    db: Session,
    document_id: UUID,
    local_user_id: UUID,
) -> Job:
    try:
        document = document_repo.get_document(db, document_id)
    except DocumentNotFound as error:
        raise JobNotFound(f"Job not found for document: {document_id}") from error
    # TODO step 2b: remove ownership plumbing.
    if document.broker_id != str(local_user_id):
        raise JobNotFound(f"Job not found for document: {document_id}")
    job = job_repo.get_job_by_document(db, document_id)
    if job is None:
        raise JobNotFound(f"Job not found for document: {document_id}")
    return job


def retry_job(db: Session, job_id: UUID, local_user_id: UUID) -> Job:
    job = job_repo.get_job(db, job_id)
    _ensure_job_document_access(db, job, local_user_id)
    if job.status == JobStatus.complete.value:
        raise JobAlreadyProcessed(f"Job already processed: {job_id}")
    retried_job = job_repo.reset_job_to_pending(db, job_id)
    log_event("job_retried", {"job_id": retried_job.id})
    return retried_job


def recover_stuck_jobs(db: Session) -> None:
    failed_jobs = job_repo.fail_stuck_processing_jobs(db)
    for job in failed_jobs:
        log_event(
            "job_failed_on_startup",
            {"job_id": job.id, "reason": "found processing on startup"},
        )


def _ensure_job_document_access(db: Session, job: Job, local_user_id: UUID) -> None:
    try:
        document = document_repo.get_document(db, UUID(job.document_id))
    except DocumentNotFound as error:
        raise JobNotFound(f"Job not found: {job.id}") from error
    # TODO step 2b: remove ownership plumbing.
    if document.broker_id != str(local_user_id):
        raise JobNotFound(f"Job not found: {job.id}")
