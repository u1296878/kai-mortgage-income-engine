from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.exceptions import JobNotFound
from app.main import app
from app.services import job_service


@pytest.fixture
def client():
    def override_db():
        yield "test-db"

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_job(**overrides):
    values = {
        "id": str(uuid4()),
        "document_id": str(uuid4()),
        "status": "pending",
        "error": None,
        "pages_total": 0,
        "pages_done": 0,
        "current_stage": None,
        "percent": 0.0,
        "created_at": datetime(2026, 5, 21, 12, 0, 0),
        "started_at": None,
        "completed_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_get_job_returns_status_response(client, monkeypatch):
    job = make_job()
    monkeypatch.setattr(job_service, "get_job_status", lambda db, job_id, user: job)

    response = client.get(f"/jobs/{job.id}")

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert "document_id" not in response.json()


def test_get_job_returns_progress_fields(client, monkeypatch):
    job = make_job(pages_total=10, pages_done=4, current_stage="ocr", percent=40.0)
    monkeypatch.setattr(job_service, "get_job_status", lambda db, job_id, user: job)

    response = client.get(f"/jobs/{job.id}")

    assert response.status_code == 200
    assert response.json()["pages_total"] == 10
    assert response.json()["pages_done"] == 4
    assert response.json()["current_stage"] == "ocr"
    assert response.json()["percent"] == 40.0


def test_get_missing_job_returns_404(client, monkeypatch):
    def raise_not_found(db, job_id, user):
        raise JobNotFound("Job not found")

    job_id = uuid4()
    monkeypatch.setattr(job_service, "get_job_status", raise_not_found)

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 404


def test_get_job_by_document_returns_job(client, monkeypatch):
    document_id = uuid4()
    job = make_job(document_id=str(document_id))
    monkeypatch.setattr(
        job_service,
        "get_job_for_document",
        lambda db, doc_id, user: job,
    )

    response = client.get(f"/documents/{document_id}/job")

    assert response.status_code == 200
    assert response.json()["id"] == job.id


def test_get_job_by_document_returns_404_when_no_job(client, monkeypatch):
    def raise_not_found(db, document_id, user):
        raise JobNotFound("Job not found")

    document_id = uuid4()
    monkeypatch.setattr(job_service, "get_job_for_document", raise_not_found)

    response = client.get(f"/documents/{document_id}/job")

    assert response.status_code == 404
