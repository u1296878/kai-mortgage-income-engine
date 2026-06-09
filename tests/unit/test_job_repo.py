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


def test_update_job_status_to_complete_sets_done_pages(test_db):
    job = make_job()
    job.pages_total = 4
    job.pages_done = 2
    test_db.add(job)
    test_db.commit()

    updated_job = job_repo.update_job_status(test_db, job.id, "complete")

    assert updated_job.pages_done == 4
    assert updated_job.current_stage == "complete"


def test_update_job_status_to_failed_sets_error(test_db):
    job = make_job()
    test_db.add(job)
    test_db.commit()

    updated_job = job_repo.update_job_status(test_db, job.id, "failed", "OCR failed")

    assert updated_job.error == "OCR failed"


def test_update_job_progress_sets_page_counts_and_stage(test_db):
    job = make_job()
    test_db.add(job)
    test_db.commit()

    updated_job = job_repo.update_job_progress(
        test_db,
        job.id,
        pages_total=10,
        pages_done=3,
        current_stage="ocr",
    )

    assert updated_job.pages_total == 10
    assert updated_job.pages_done == 3
    assert updated_job.current_stage == "ocr"
    assert updated_job.percent == 30.0


def test_reset_job_to_pending_clears_progress(test_db):
    job = make_job(status="failed", error="OCR failed")
    job.pages_total = 10
    job.pages_done = 4
    job.current_stage = "failed"
    test_db.add(job)
    test_db.commit()

    reset_job = job_repo.reset_job_to_pending(test_db, job.id)

    assert reset_job.pages_total == 0
    assert reset_job.pages_done == 0
    assert reset_job.current_stage is None


def test_fail_stuck_processing_jobs_marks_processing_jobs_failed(test_db):
    processing_job = make_job(status="processing")
    processing_job.started_at = datetime.now(timezone.utc)
    pending_job = make_job(status="pending")
    complete_job = make_job(status="complete")
    failed_job = make_job(status="failed")
    test_db.add_all([processing_job, pending_job, complete_job, failed_job])
    test_db.commit()

    failed_jobs = job_repo.fail_stuck_processing_jobs(test_db)
    test_db.refresh(processing_job)
    test_db.refresh(pending_job)
    test_db.refresh(complete_job)
    test_db.refresh(failed_job)

    assert [job.id for job in failed_jobs] == [processing_job.id]
    assert processing_job.status == "failed"
    assert processing_job.error == job_repo.STUCK_PROCESSING_ERROR
    assert processing_job.completed_at is not None
    assert pending_job.status == "pending"
    assert complete_job.status == "complete"
    assert failed_job.status == "failed"
