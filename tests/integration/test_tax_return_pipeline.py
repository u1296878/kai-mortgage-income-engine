from io import BytesIO

from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.dependencies import get_db
from app.main import app
from app.repositories import (
    job_repo,
    rental_calculation_repo,
    result_repo,
    self_employment_calculation_repo,
)
from app.storage import local_storage
from app.workers.job_worker import process_next_job
from tests.auth_helpers import auth_headers


def test_tax_return_upload_produces_real_fields(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    client = TestClient(app)
    headers = auth_headers(client)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("tax-return.pdf", _tax_return_pdf_bytes(), "application/pdf")},
            data={"doc_type": "tax_return"},
            headers=headers,
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
        assert result.annual_income is None
        assert result.confidence == "medium"
        assert "AGI shown for reference only" in result.notes
    finally:
        app.dependency_overrides.clear()


def test_tax_return_upload_with_schedules_creates_reviewable_drafts(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    client = TestClient(app)
    headers = auth_headers(client)
    case = client.post("/cases", json={"title": "Schedule E"}, headers=headers).json()

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("tax-return.pdf", _tax_return_schedule_e_pdf_bytes(), "application/pdf")},
            data={"doc_type": "tax_return", "case_id": case["id"]},
            headers=headers,
        )
        assert response.status_code == 200
        job = job_repo.get_job_by_document(test_db, response.json()["id"])

        processed = process_next_job(test_db)
        result = result_repo.get_result_by_job(test_db, job.id)
        fields = {field["field"]: field for field in result.extracted_fields}
        calculations = rental_calculation_repo.list_by_case(test_db, case["id"])
        self_employment = self_employment_calculation_repo.list_by_case(test_db, case["id"])

        assert processed is True
        assert fields["schedule_e_present"]["value"] == 1.0
        assert fields["schedule_e_property_a_gross_rents"]["value"] == 22480.0
        assert fields["schedule_e_property_b_gross_rents"]["value"] == 13500.0
        assert fields["schedule_e_net_rental_income"]["value"] == -1303.0
        assert fields["schedule_c_business_1_net_profit"]["value"] == 50000.0
        assert result.annual_income is None
        assert len(calculations) == 2
        assert len(self_employment) == 1
        assert calculations[0].included is True
        assert self_employment[0].included is True
        assert calculations[0].qualifying_monthly > 0
        assert self_employment[0].qualifying_monthly > 0
        assert "per-schedule drafts" in result.notes
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


def _tax_return_schedule_e_pdf_bytes() -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(50, 740, "Form 1040 U.S. Individual Income Tax Return 2024")
    c.drawString(50, 710, "Filing Status: Head of household")
    c.drawString(50, 650, "1a Total amount from Form(s) W-2, box 1")
    c.drawString(500, 650, "76769.00")
    c.drawString(50, 610, "9 Total income")
    c.drawString(500, 610, "75150.00")
    c.drawString(50, 570, "11 Adjusted gross income")
    c.drawString(500, 570, "73168.00")
    c.showPage()
    c.drawString(50, 740, "Schedule E Supplemental Income and Loss")
    c.drawString(50, 700, "1a Physical address of each property")
    c.drawString(50, 680, "A 131 E 500 S Provo UT 84606")
    c.drawString(50, 660, "B 2221 Corby Blvd South Bend IN 46615")
    c.drawString(50, 640, "A")
    c.drawString(420, 640, "366")
    c.drawString(50, 620, "B")
    c.drawString(420, 620, "240")
    c.drawString(50, 600, "Income:")
    c.drawString(420, 600, "A")
    c.drawString(500, 600, "B")
    c.drawString(580, 600, "C")
    c.drawString(50, 580, "3 Rents received")
    c.drawString(420, 580, "22480.00")
    c.drawString(500, 580, "13500.00")
    c.drawString(50, 560, "9 Insurance")
    c.drawString(420, 560, "211.00")
    c.drawString(50, 540, "12 Mortgage interest")
    c.drawString(500, 540, "5264.00")
    c.drawString(50, 520, "13 Other interest")
    c.drawString(420, 520, "4280.00")
    c.drawString(50, 500, "16 Taxes")
    c.drawString(420, 500, "1677.00")
    c.drawString(500, 500, "889.00")
    c.drawString(50, 480, "18 Depreciation expense")
    c.drawString(420, 480, "8116.00")
    c.drawString(500, 480, "4049.00")
    c.drawString(50, 460, "20 Total expenses")
    c.drawString(420, 460, "19943.00")
    c.drawString(500, 460, "12597.00")
    c.drawString(50, 420, "23a Total line 3 rental properties")
    c.drawString(500, 420, "35980.00")
    c.drawString(50, 400, "23c Total line 12 properties")
    c.drawString(500, 400, "5264.00")
    c.drawString(50, 380, "23d Total line 18 properties")
    c.drawString(500, 380, "12165.00")
    c.drawString(50, 360, "23e Total line 20 properties")
    c.drawString(500, 360, "32540.00")
    c.drawString(50, 320, "26 Total rental real estate income or loss")
    c.drawString(500, 280, "26")
    c.drawString(540, 280, "(1303.00)")
    c.showPage()
    c.drawString(50, 740, "Schedule C Profit or Loss From Business")
    c.drawString(50, 680, "6 Other income")
    c.drawString(500, 680, "5000.00")
    c.drawString(50, 660, "12 Depletion")
    c.drawString(500, 660, "500.00")
    c.drawString(50, 640, "13 Depreciation")
    c.drawString(500, 640, "8000.00")
    c.drawString(50, 620, "24b Meals")
    c.drawString(500, 620, "2000.00")
    c.drawString(50, 600, "27a Other expenses")
    c.drawString(500, 600, "700.00")
    c.drawString(50, 580, "30 Business use of home")
    c.drawString(500, 580, "3000.00")
    c.drawString(50, 560, "31 Net profit or loss")
    c.drawString(500, 560, "50000.00")
    c.drawString(50, 520, "44a Business miles")
    c.drawString(500, 520, "1000")
    c.save()
    return buffer.getvalue()
