from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user, get_db
from app.exceptions import DocumentNotFound, Unauthorized
from app.main import app
from app.services import document_service


@pytest.fixture
def client():
    def override_db():
        yield "test-db"

    def override_user():
        return SimpleNamespace(id=str(uuid4()), role="broker")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_document(**overrides):
    values = {
        "id": str(uuid4()),
        "filename": "paystub.pdf",
        "doc_type": "pay_stub",
        "case_id": None,
        "storage_path": "internal/path/paystub.pdf",
        "uploaded_at": datetime(2026, 5, 20, 12, 0, 0),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_upload_endpoint_returns_document_response(client, monkeypatch):
    document = make_document()
    monkeypatch.setattr(
        document_service,
        "upload_document",
        lambda db, file, doc_type, current_user, case_id=None: document,
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("paystub.pdf", b"contents", "application/pdf")},
        data={"doc_type": "pay_stub"},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "paystub.pdf"
    assert "storage_path" not in response.json()


def test_upload_invalid_doc_type_returns_422(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("paystub.pdf", b"contents", "application/pdf")},
        data={"doc_type": "passport"},
    )

    assert response.status_code == 422


def test_get_document_returns_document(client, monkeypatch):
    document = make_document()
    monkeypatch.setattr(
        document_service,
        "get_document",
        lambda db, document_id, current_user: document,
    )

    response = client.get(f"/documents/{document.id}")

    assert response.status_code == 200
    assert response.json()["id"] == document.id
    assert "storage_path" not in response.json()


def test_get_missing_document_returns_404(client, monkeypatch):
    def raise_not_found(db, document_id, current_user):
        raise DocumentNotFound("Document not found")

    document_id = uuid4()
    monkeypatch.setattr(document_service, "get_document", raise_not_found)

    response = client.get(f"/documents/{document_id}")

    assert response.status_code == 404


def test_get_document_file_returns_stream(client, monkeypatch, tmp_path):
    file_path = tmp_path / "doc.pdf"
    file_path.write_bytes(b"%PDF-1.4\ntest\n")
    document = make_document(filename="doc.pdf")
    monkeypatch.setattr(
        document_service,
        "get_document_file",
        lambda db, document_id, current_user: (document, file_path),
    )

    response = client.get(f"/documents/{document.id}/file")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4\ntest\n"


def test_get_document_file_forbidden_returns_403(client, monkeypatch):
    def raise_forbidden(db, document_id, current_user):
        raise Unauthorized("forbidden")

    monkeypatch.setattr(document_service, "get_document_file", raise_forbidden)

    response = client.get(f"/documents/{uuid4()}/file")

    assert response.status_code == 403


def test_patch_case_link_returns_updated_document(client, monkeypatch):
    case_id = uuid4()
    document = make_document(case_id=str(case_id))
    monkeypatch.setattr(
        document_service,
        "link_document_to_case",
        lambda db, document_id, linked_case_id, current_user: document,
    )

    response = client.patch(
        f"/documents/{document.id}/case",
        json={"case_id": str(case_id)},
    )

    assert response.status_code == 200
    assert response.json()["case_id"] == str(case_id)


def test_upload_with_missing_case_returns_404(client, monkeypatch):
    def raise_not_found(db, file, doc_type, current_user, case_id=None):
        raise DocumentNotFound("Document not found")

    monkeypatch.setattr(document_service, "upload_document", raise_not_found)

    response = client.post(
        "/documents/upload",
        files={"file": ("paystub.pdf", b"contents", "application/pdf")},
        data={"doc_type": "pay_stub", "case_id": str(uuid4())},
    )

    assert response.status_code == 404
