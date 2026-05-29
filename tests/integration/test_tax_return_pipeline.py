from io import BytesIO

from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.dependencies import get_db
from app.main import app
from app.repositories import job_repo, result_repo
from app.services import document_service
from app.workers.job_worker import process_next_job


def test_tax_return_upload_produces_real_fields(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    client = TestClient(app)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("tax-return.pdf", _tax_return_pdf_bytes(), "application/pdf")},
            data={"doc_type": "tax_return"},
        )
        assert response.status_code == 200
        job = job_repo.get_job_by_document(test_db, response.json()["id"])

        processed = process_next_job(test_db)
        result = result_repo.get_result_by_job(test_db, job.id)
        fields = {field["field"]: field for field in result.extracted_fields}

        assert processed is True
        assert fields["agi"]["value"] == 79000.0
        assert fields["wages"]["value"] == 85000.0
        assert fields["tax_year"]["value"] == 2023.0
        assert fields["agi"]["bounding_box"] != {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0}
        assert fields["wages"]["bounding_box"] != {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0}
        assert fields["tax_year"]["bounding_box"] != {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0}
        assert result.annual_income == 79000.0
        assert result.confidence == "high"
    finally:
        app.dependency_overrides.clear()


def _tax_return_pdf_bytes() -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(50, 740, "Form 1040 U.S. Individual Income Tax Return 2023")
    c.drawString(50, 710, "Filing Status: Single")
    c.drawString(50, 650, "1a Total amount from Form(s) W-2, box 1")
    c.drawString(500, 650, "85000.00")
    c.drawString(50, 610, "9 Total income")
    c.drawString(500, 610, "90000.00")
    c.drawString(50, 570, "11 Adjusted gross income")
    c.drawString(500, 570, "79000.00")
    c.showPage()
    c.drawString(50, 740, "Schedule C Profit or Loss From Business")
    c.drawString(50, 680, "31 Net profit or loss")
    c.drawString(500, 680, "5000.00")
    c.save()
    return buffer.getvalue()
