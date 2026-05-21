from uuid import uuid4

import pytest

from app.exceptions import JobNotFound
from app.models.job import Job
from app.services import job_service


def test_create_job_for_document_returns_pending_job(test_db):
    document_id = uuid4()

    job = job_service.create_job_for_document(test_db, document_id)

    assert job.status == "pending"


def test_create_job_sets_document_id(test_db):
    document_id = uuid4()

    job = job_service.create_job_for_document(test_db, document_id)

    assert job.document_id == str(document_id)


def test_get_job_status_returns_job(test_db):
    job = Job(document_id=str(uuid4()))
    test_db.add(job)
    test_db.commit()

    result = job_service.get_job_status(test_db, job.id)

    assert result.id == job.id


def test_get_missing_job_raises(test_db):
    job_id = uuid4()

    with pytest.raises(JobNotFound):
        job_service.get_job_status(test_db, job_id)
