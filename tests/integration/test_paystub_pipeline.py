from io import BytesIO

from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.dependencies import get_db
from app.main import app
from app.repositories import job_repo, result_repo
from app.storage import local_storage
from app.workers.job_worker import process_next_job
from tests.local_user_helpers import local_headers


def test_paystub_upload_produces_real_fields(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    client = TestClient(app)
    headers = local_headers(client)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("paystub.pdf", _paystub_pdf_bytes(), "application/pdf")},
            data={"doc_type": "pay_stub"},
            headers=headers,
        )
        assert response.status_code == 200
        document_id = response.json()["id"]
        job = job_repo.get_job_by_document(test_db, document_id)
        process_next_job(test_db)
        result = result_repo.get_result_by_job(test_db, job.id)
        gross_ytd = next(field for field in result.extracted_fields if field["field"] == "gross_ytd")

        assert gross_ytd["value"] == 42500.0
        assert gross_ytd["bounding_box"] != {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0}
        assert result.annual_income is not None
    finally:
        app.dependency_overrides.clear()


def _paystub_pdf_bytes() -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(50, 700, "Pay Date: 2024-05-15")
    c.drawString(50, 670, "Pay Frequency: Biweekly")
    c.drawString(50, 640, "Income Type: Salary")
    c.drawString(50, 590, "Gross Pay:")
    c.drawString(300, 590, "$3,269.23")
    c.drawString(50, 560, "YTD Gross:")
    c.drawString(300, 560, "$42,500.00")
    c.drawString(50, 530, "Bonus YTD:")
    c.drawString(300, 530, "$2,500.00")
    c.save()
    return buffer.getvalue()
