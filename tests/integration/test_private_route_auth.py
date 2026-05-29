from uuid import uuid4

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


def test_private_routes_require_authentication(client):
    case_id = uuid4()
    job_id = uuid4()

    cases_response = client.get("/cases")
    upload_response = client.post(
        "/documents/upload",
        files={"file": ("w2.pdf", b"contents", "application/pdf")},
        data={"doc_type": "w2"},
    )
    job_response = client.get(f"/jobs/{job_id}")
    summary_response = client.get(f"/cases/{case_id}/summary")

    assert cases_response.status_code == 401
    assert upload_response.status_code == 401
    assert job_response.status_code == 401
    assert summary_response.status_code == 401


def test_broker_case_creation_uses_current_user_id(client):
    broker_headers, broker_id = auth_user(client)

    response = client.post(
        "/cases",
        json={"title": "Spoof attempt", "broker_id": str(uuid4())},
        headers=broker_headers,
    )

    assert response.status_code == 200
    assert response.json()["broker_id"] == broker_id
