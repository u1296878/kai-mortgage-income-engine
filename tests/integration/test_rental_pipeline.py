from io import BytesIO

from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.dependencies import get_db
from app.main import app
from app.repositories import job_repo, result_repo
from app.storage import local_storage
from app.workers.job_worker import process_next_job


def test_rental_upload_produces_real_fields(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    client = TestClient(app)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("rental.pdf", _rental_pdf_bytes(), "application/pdf")},
            data={"doc_type": "other"},
        )
        assert response.status_code == 200
        job = job_repo.get_job_by_document(test_db, response.json()["id"])

        processed = process_next_job(test_db)
        result = result_repo.get_result_by_job(test_db, job.id)
        fields = {field["field"]: field for field in result.extracted_fields}

        assert processed is True
        assert fields["rental_gross_income"]["value"] == 24000.0
        assert fields["rental_expenses"]["value"] == 6000.0
        assert fields["rental_net_income"]["value"] == 18000.0
        assert fields["reported_income"]["value"] == 18000.0
        assert fields["tax_year"]["value"] == 2023.0
        assert fields["property_address"]["raw_text"] == "123 Sample Rental Ave"
        assert result.annual_income == 18000.0
        assert result.confidence == "low"
        for field_name in ("reported_income", "rental_net_income", "rental_gross_income", "rental_expenses", "tax_year"):
            assert fields[field_name]["bounding_box"] != {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0}
    finally:
        app.dependency_overrides.clear()


def _rental_pdf_bytes() -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(50, 740, "Schedule E Supplemental Income and Loss 2023")
    c.drawString(50, 700, "Property Address: 123 Sample Rental Ave")
    c.drawString(50, 640, "3 Rents received")
    c.drawString(500, 640, "24000.00")
    c.drawString(50, 600, "20 Total expenses")
    c.drawString(500, 600, "6000.00")
    c.drawString(50, 560, "21 Income or loss")
    c.drawString(500, 560, "18000.00")
    c.save()
    return buffer.getvalue()
