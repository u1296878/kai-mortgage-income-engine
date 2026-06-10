import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.storage import local_storage
from tests.local_user_helpers import local_user


@pytest.fixture
def client(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_document_owner_can_fetch_document_file(client):
    owner_headers, _ = local_user(client)
    expected_bytes = b"%PDF-1.4\nowner\n"
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", expected_bytes, "application/pdf")},
        data={"doc_type": "w2"},
        headers=owner_headers,
    )

    response = client.get(
        f"/documents/{upload.json()['id']}/file",
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == expected_bytes


def test_local_endpoint_returns_uploaded_document_file(client):
    owner_headers, _ = local_user(client)
    local_headers, _ = local_user(client)
    expected_bytes = b"%PDF-1.4\nowner\n"
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", expected_bytes, "application/pdf")},
        data={"doc_type": "w2"},
        headers=owner_headers,
    )

    response = client.get(
        f"/documents/{upload.json()['id']}/file",
        headers=local_headers,
    )

    assert response.status_code == 200
    assert response.content == expected_bytes
