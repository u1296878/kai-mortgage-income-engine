from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.storage import local_storage
from app.workers.job_worker import process_next_job
from tests.auth_helpers import auth_headers


def test_broker_workflow_upload_to_verified_income(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    client = TestClient(app)
    headers = auth_headers(client)

    try:
        case_response = client.post(
            "/cases",
            json={"title": "Johnson Refinance 2024", "broker_id": str(uuid4())},
            headers=headers,
        )
        assert case_response.status_code == 200
        case_id = case_response.json()["id"]

        upload_response = client.post(
            "/documents/upload",
            files={"file": ("w2.pdf", _w2_pdf_bytes(), "application/pdf")},
            data={"doc_type": "w2"},
            headers=headers,
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["id"]

        link_response = client.patch(
            f"/documents/{document_id}/case",
            json={"case_id": case_id},
            headers=headers,
        )
        assert link_response.status_code == 200

        job_response = client.get(f"/documents/{document_id}/job", headers=headers)
        assert job_response.status_code == 200
        assert job_response.json()["status"] == "pending"
        job_id = job_response.json()["id"]

        processed = process_next_job(test_db)
        assert processed is True

        completed_job_response = client.get(f"/jobs/{job_id}", headers=headers)
        assert completed_job_response.status_code == 200
        assert completed_job_response.json()["status"] == "complete"

        result_response = client.get(f"/jobs/{job_id}/result", headers=headers)
        assert result_response.status_code == 200
        assert result_response.json()["annual_income"] is not None
        assert result_response.json()["extracted_fields"]

        summary_response = client.get(f"/cases/{case_id}/summary", headers=headers)
        assert summary_response.status_code == 200
        assert summary_response.json()["total_annual_income"] is not None
        sources = summary_response.json()["sources"]
        assert sources
        assert all(source["document_id"] == document_id for source in sources)
        assert all("page" in source for source in sources)
        assert all("bounding_box" in source for source in sources)
    finally:
        app.dependency_overrides.clear()


def _w2_pdf_bytes() -> bytes:
    stream = (
        "BT /F1 12 Tf 50 700 Td (Wages, tips, other compensation) Tj "
        "200 0 Td (85000.00) Tj -200 -40 Td "
        "(Federal income tax withheld) Tj 200 0 Td (12000.00) Tj ET"
    )
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n".encode(),
    ]
    content = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(content))
        content += obj
    xref = len(content)
    content += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode()
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n".encode()
    content += f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return content
