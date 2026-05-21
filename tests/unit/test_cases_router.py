from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.exceptions import CaseNotFound
from app.main import app
from app.services import case_service


@pytest.fixture
def client():
    def override_db():
        yield "test-db"

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_case(**overrides):
    values = {
        "id": str(uuid4()),
        "broker_id": str(uuid4()),
        "title": "Johnson Refinance 2024",
        "status": "open",
        "created_at": datetime(2026, 5, 21, 12, 0, 0),
        "updated_at": datetime(2026, 5, 21, 12, 0, 0),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_create_case_returns_case_response(client, monkeypatch):
    case = make_case()
    monkeypatch.setattr(case_service, "create_case", lambda db, title, broker_id: case)

    response = client.post(
        "/cases",
        json={"title": case.title, "broker_id": case.broker_id},
    )

    assert response.status_code == 200
    assert response.json()["title"] == case.title


def test_list_cases_returns_list(client, monkeypatch):
    case = make_case()
    monkeypatch.setattr(case_service, "list_cases", lambda db, broker_id=None: [case])

    response = client.get("/cases")

    assert response.status_code == 200
    assert response.json()[0]["id"] == case.id


def test_get_case_returns_case(client, monkeypatch):
    case = make_case()
    monkeypatch.setattr(case_service, "get_case", lambda db, case_id: case)

    response = client.get(f"/cases/{case.id}")

    assert response.status_code == 200
    assert response.json()["id"] == case.id


def test_get_missing_case_returns_404(client, monkeypatch):
    def raise_not_found(db, case_id):
        raise CaseNotFound("Case not found")

    case_id = uuid4()
    monkeypatch.setattr(case_service, "get_case", raise_not_found)

    response = client.get(f"/cases/{case_id}")

    assert response.status_code == 404


def test_get_case_with_documents_returns_documents(client, monkeypatch):
    document = SimpleNamespace(
        id=str(uuid4()),
        filename="w2.pdf",
        doc_type="w2",
        case_id=str(uuid4()),
        uploaded_at=datetime(2026, 5, 21, 12, 0, 0),
    )
    case = make_case(documents=[document])
    monkeypatch.setattr(
        case_service,
        "get_case_with_documents",
        lambda db, case_id, broker_id=None: case,
    )

    response = client.get(f"/cases/{case.id}/documents")

    assert response.status_code == 200
    assert response.json()["documents"][0]["filename"] == "w2.pdf"


def test_patch_case_returns_updated_case(client, monkeypatch):
    case = make_case(title="Updated Title")
    monkeypatch.setattr(case_service, "update_case", lambda db, case_id, updates: case)

    response = client.patch(f"/cases/{case.id}", json={"title": "Updated Title"})

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_delete_case_returns_204(client, monkeypatch):
    case_id = uuid4()
    monkeypatch.setattr(case_service, "delete_case", lambda db, case_id: None)

    response = client.delete(f"/cases/{case_id}")

    assert response.status_code == 204
