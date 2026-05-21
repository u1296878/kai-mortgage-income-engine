from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.services import document_service
from app.workers.job_worker import process_next_job


def test_broker_workflow_upload_to_verified_income(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    client = TestClient(app)
    broker_id = str(uuid4())

    try:
        case_response = client.post(
            "/cases",
            json={"title": "Johnson Refinance 2024", "broker_id": broker_id},
        )
        assert case_response.status_code == 200
        case_id = case_response.json()["id"]

        upload_response = client.post(
            "/documents/upload",
            files={"file": ("w2.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={"doc_type": "w2"},
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["id"]

        link_response = client.patch(
            f"/documents/{document_id}/case",
            json={"case_id": case_id},
        )
        assert link_response.status_code == 200

        job_response = client.get(f"/documents/{document_id}/job")
        assert job_response.status_code == 200
        assert job_response.json()["status"] == "pending"
        job_id = job_response.json()["id"]

        processed = process_next_job(test_db)
        assert processed is True

        completed_job_response = client.get(f"/jobs/{job_id}")
        assert completed_job_response.status_code == 200
        assert completed_job_response.json()["status"] == "complete"

        result_response = client.get(f"/jobs/{job_id}/result")
        assert result_response.status_code == 200
        assert result_response.json()["annual_income"] is not None
        assert result_response.json()["extracted_fields"]

        summary_response = client.get(f"/cases/{case_id}/summary")
        assert summary_response.status_code == 200
        assert summary_response.json()["total_annual_income"] is not None
        sources = summary_response.json()["sources"]
        assert sources
        assert all(source["document_id"] == document_id for source in sources)
        assert all("page" in source for source in sources)
        assert all("bounding_box" in source for source in sources)
    finally:
        app.dependency_overrides.clear()
