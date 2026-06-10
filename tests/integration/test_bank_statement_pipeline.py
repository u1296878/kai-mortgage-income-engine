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


def test_bank_statement_upload_produces_real_fields(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    client = TestClient(app)
    headers = local_headers(client)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("bank.pdf", _bank_statement_pdf_bytes(), "application/pdf")},
            data={"doc_type": "bank_statement"},
            headers=headers,
        )
        assert response.status_code == 200
        job = job_repo.get_job_by_document(test_db, response.json()["id"])

        processed = process_next_job(test_db)
        result = result_repo.get_result_by_job(test_db, job.id)
        fields = {field["field"]: field for field in result.extracted_fields}

        assert processed is True
        assert fields["total_deposits"]["value"] == 15000.0
        assert fields["months_sampled"]["value"] == 3.0
        assert fields["average_monthly_deposit"]["value"] == 5000.0
        assert fields["statement_start_date"]["raw_text"] == "2024-01-01"
        assert fields["statement_end_date"]["raw_text"] == "2024-03-31"
        assert result.annual_income == 60000.0
        assert result.confidence == "low"
        for field_name in ("average_monthly_deposit", "months_sampled", "total_deposits"):
            assert fields[field_name]["bounding_box"] != {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0}
    finally:
        app.dependency_overrides.clear()


def _bank_statement_pdf_bytes() -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(50, 740, "Sample Bank")
    c.drawString(50, 710, "Account Holder: Sample Borrower")
    c.drawString(50, 690, "Account Number: ****1234")
    c.drawString(50, 660, "Statement Period: 2024-01-01 to 2024-03-31")
    c.drawString(50, 620, "Beginning Balance 1200.00")
    c.drawString(50, 580, "2024-01-15 Payroll Deposit ACME Corp")
    c.drawString(500, 580, "5000.00")
    c.drawString(50, 550, "2024-01-20 Debit Card Purchase Grocery Store")
    c.drawString(500, 550, "-125.00")
    c.drawString(50, 520, "2024-02-01 ATM Withdrawal")
    c.drawString(500, 520, "-200.00")
    c.drawString(50, 490, "2024-02-15 Direct Deposit ACME Corp")
    c.drawString(500, 490, "5000.00")
    c.drawString(50, 460, "2024-03-15 ACH Credit Payroll")
    c.drawString(500, 460, "5000.00")
    c.drawString(50, 420, "Ending Balance 16200.00")
    c.drawString(50, 380, "Total Deposits and Credits")
    c.drawString(500, 380, "15000.00")
    c.save()
    return buffer.getvalue()
