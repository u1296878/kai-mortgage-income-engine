from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.repositories import job_repo, result_repo
from app.services import document_service
from app.workers.job_worker import process_next_job


def test_w2_upload_produces_real_fields(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    client = TestClient(app)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("w2.pdf", _w2_pdf_bytes(), "application/pdf")},
            data={"doc_type": "w2"},
        )
        assert response.status_code == 200
        document_id = response.json()["id"]
        job = job_repo.get_job_by_document(test_db, document_id)

        processed = process_next_job(test_db)
        result = result_repo.get_result_by_job(test_db, job.id)
        wages = next(field for field in result.extracted_fields if field["field"] == "w2_wages")

        assert processed is True
        assert wages["value"] == 85000.00
        assert wages["bounding_box"] != {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0}
    finally:
        app.dependency_overrides.clear()


def _w2_pdf_bytes() -> bytes:
    stream = (
        "BT /F1 12 Tf "
        "50 700 Td (Wages, tips, other compensation) Tj "
        "200 0 Td (85000.00) Tj "
        "-200 -40 Td (Federal income tax withheld) Tj "
        "200 0 Td (12000.00) Tj ET"
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
