from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import JobNotFound
from app.models.job import Job
from app.repositories import job_repo


def create_job_for_document(db: Session, document_id: UUID) -> Job:
    job = Job(document_id=str(document_id))
    saved_job = job_repo.create_job(db, job)
    log_event(
        "job_created",
        {"job_id": saved_job.id, "document_id": saved_job.document_id},
    )
    return saved_job


def get_job_status(db: Session, job_id: UUID) -> Job:
    return job_repo.get_job(db, job_id)


def get_job_for_document(db: Session, document_id: UUID) -> Job:
    job = job_repo.get_job_by_document(db, document_id)
    if job is None:
        raise JobNotFound(f"Job not found for document: {document_id}")
    return job
