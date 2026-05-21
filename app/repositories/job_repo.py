from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import JobNotFound
from app.models.job import Job
from app.models.job_status import JobStatus


def create_job(db: Session, job: Job) -> Job:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: UUID) -> Job:
    job = db.get(Job, str(job_id))
    if job is None:
        raise JobNotFound(f"Job not found: {job_id}")
    return job


def get_job_by_document(db: Session, document_id: UUID) -> Job | None:
    statement = select(Job).where(Job.document_id == str(document_id))
    return db.scalars(statement).first()


def claim_next_pending_job(db: Session) -> Job | None:
    statement = (
        select(Job)
        .where(Job.status == JobStatus.pending.value)
        .order_by(Job.created_at)
        # Workers lock and skip already locked rows so one job is claimed once.
        .with_for_update(skip_locked=True)
    )
    job = db.scalars(statement).first()
    if job is None:
        return None
    job.status = JobStatus.processing.value
    job.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def update_job_status(
    db: Session,
    job_id: UUID,
    status: str,
    error: str | None = None,
) -> Job:
    job = get_job(db, job_id)
    job.status = status
    job.error = error
    if status in {JobStatus.complete.value, JobStatus.failed.value}:
        job.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job
