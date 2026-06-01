import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.storage import local_storage
from tests.auth_helpers import auth_user


@pytest.fixture
def client(test_db, tmp_path, monkeypatch):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_document_file_requires_authentication(client):
    owner_headers, _ = auth_user(client)
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"%PDF-1.4\nowner\n", "application/pdf")},
        data={"doc_type": "w2"},
        headers=owner_headers,
    )

    response = client.get(f"/documents/{upload.json()['id']}/file")

    assert response.status_code == 401


def test_document_owner_can_fetch_document_file(client):
    owner_headers, _ = auth_user(client)
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


def test_wrong_broker_gets_forbidden_for_document_file(client):
    owner_headers, _ = auth_user(client)
    other_broker_headers, _ = auth_user(client)
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"%PDF-1.4\nowner\n", "application/pdf")},
        data={"doc_type": "w2"},
        headers=owner_headers,
    )

    response = client.get(
        f"/documents/{upload.json()['id']}/file",
        headers=other_broker_headers,
    )

    assert response.status_code == 403


def test_manager_can_fetch_any_document_file(client):
    owner_headers, _ = auth_user(client)
    manager_headers, _ = auth_user(client, role="manager")
    expected_bytes = b"%PDF-1.4\nowner\n"
    upload = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", expected_bytes, "application/pdf")},
        data={"doc_type": "w2"},
        headers=owner_headers,
    )

    response = client.get(
        f"/documents/{upload.json()['id']}/file",
        headers=manager_headers,
    )

    assert response.status_code == 200
    assert response.content == expected_bytes
