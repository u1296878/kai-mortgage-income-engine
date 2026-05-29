from uuid import uuid4

import pytest

from app.exceptions import JobNotFound
from app.models.document import Document
from app.models.job import Job
from app.models.user import User
from app.services import job_service


def make_user(user_id=None, role="broker"):
    return User(
        id=str(user_id or uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="hash",
        role=role,
    )


def test_create_job_for_document_returns_pending_job(test_db):
    document_id = uuid4()

    job = job_service.create_job_for_document(test_db, document_id)

    assert job.status == "pending"


def test_create_job_sets_document_id(test_db):
    document_id = uuid4()

    job = job_service.create_job_for_document(test_db, document_id)

    assert job.document_id == str(document_id)


def test_get_job_status_returns_job(test_db):
    broker_id = uuid4()
    document = Document(
        id=str(uuid4()),
        filename="w2.pdf",
        doc_type="w2",
        storage_path="storage/path/w2.pdf",
        broker_id=str(broker_id),
    )
    job = Job(document_id=document.id)
    test_db.add_all([document, job])
    test_db.commit()

    result = job_service.get_job_status(test_db, job.id, make_user(broker_id))

    assert result.id == job.id


def test_get_missing_job_raises(test_db):
    job_id = uuid4()

    with pytest.raises(JobNotFound):
        job_service.get_job_status(test_db, job_id, make_user())
