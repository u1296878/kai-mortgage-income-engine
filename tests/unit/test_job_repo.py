from datetime import datetime, timezone
from uuid import uuid4

from app.models.job import Job
from app.repositories import job_repo


def make_job(status="pending", error=None):
    return Job(
        id=str(uuid4()),
        document_id=str(uuid4()),
        status=status,
        error=error,
    )


def test_claim_next_pending_job_returns_job(test_db):
    job = make_job()
    test_db.add(job)
    test_db.commit()

    claimed_job = job_repo.claim_next_pending_job(test_db)

    assert claimed_job.id == job.id


def test_claim_next_pending_job_sets_status_to_processing(test_db):
    job = make_job()
    test_db.add(job)
    test_db.commit()

    claimed_job = job_repo.claim_next_pending_job(test_db)

    assert claimed_job.status == "processing"


def test_claim_next_pending_job_returns_none_when_queue_empty(test_db):
    claimed_job = job_repo.claim_next_pending_job(test_db)

    assert claimed_job is None


def test_claim_does_not_return_already_processing_job(test_db):
    job = make_job(status="processing")
    test_db.add(job)
    test_db.commit()

    claimed_job = job_repo.claim_next_pending_job(test_db)

    assert claimed_job is None


def test_update_job_status_to_complete_sets_completed_at(test_db):
    job = make_job()
    test_db.add(job)
    test_db.commit()

    updated_job = job_repo.update_job_status(test_db, job.id, "complete")

    assert updated_job.completed_at is not None


def test_update_job_status_to_failed_sets_error(test_db):
    job = make_job()
    test_db.add(job)
    test_db.commit()

    updated_job = job_repo.update_job_status(test_db, job.id, "failed", "OCR failed")

    assert updated_job.error == "OCR failed"


def test_reset_processing_jobs_to_pending_clears_started_at(test_db):
    processing_job = make_job(status="processing")
    processing_job.started_at = datetime.now(timezone.utc)
    failed_job = make_job(status="failed")
    test_db.add_all([processing_job, failed_job])
    test_db.commit()

    recovered_jobs = job_repo.reset_processing_jobs_to_pending(test_db)
    test_db.refresh(processing_job)
    test_db.refresh(failed_job)

    assert [job.id for job in recovered_jobs] == [processing_job.id]
    assert processing_job.status == "pending"
    assert processing_job.started_at is None
    assert failed_job.status == "failed"
