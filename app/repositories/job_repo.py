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


def list_jobs_by_status(db: Session, status: str) -> list[Job]:
    statement = select(Job).where(Job.status == status).order_by(Job.created_at)
    return list(db.scalars(statement).all())


STUCK_PROCESSING_ERROR = (
    "auto-failed on startup: was processing during a restart; retry manually"
)


def fail_stuck_processing_jobs(db: Session) -> list[Job]:
    jobs = list_jobs_by_status(db, JobStatus.processing.value)
    if not jobs:
        return []
    completed_at = datetime.now(timezone.utc)
    for job in jobs:
        job.status = JobStatus.failed.value
        job.error = STUCK_PROCESSING_ERROR
        job.completed_at = completed_at
    db.commit()
    for job in jobs:
        db.refresh(job)
    return jobs


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
    job.current_stage = "processing"
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
    if status == JobStatus.complete.value:
        job.current_stage = "complete"
        if job.pages_total > 0:
            job.pages_done = job.pages_total
    if status == JobStatus.failed.value:
        job.current_stage = "failed"
    db.commit()
    db.refresh(job)
    return job


def update_job_progress(
    db: Session,
    job_id: UUID,
    pages_total: int | None = None,
    pages_done: int | None = None,
    current_stage: str | None = None,
) -> Job:
    job = get_job(db, job_id)
    if pages_total is not None:
        job.pages_total = pages_total
    if pages_done is not None:
        job.pages_done = pages_done
    if current_stage is not None:
        job.current_stage = current_stage
    db.commit()
    db.refresh(job)
    return job


def reset_job_to_pending(db: Session, job_id: UUID) -> Job:
    job = get_job(db, job_id)
    job.status = JobStatus.pending.value
    job.error = None
    job.pages_total = 0
    job.pages_done = 0
    job.current_stage = None
    job.started_at = None
    job.completed_at = None
    db.commit()
    db.refresh(job)
    return job


def delete_job_by_document(db: Session, document_id: UUID) -> None:
    job = get_job_by_document(db, document_id)
    if job is not None:
        db.delete(job)
        db.commit()
