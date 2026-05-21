from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.exceptions import ResultNotFound
from app.main import app
from app.services import result_service


@pytest.fixture
def client():
    def override_db():
        yield "test-db"

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_field(document_id):
    return {
        "field": "w2_wages",
        "value": 85000.00,
        "document_id": str(document_id),
        "page": 1,
        "bounding_box": {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0},
    }


def make_result(**overrides):
    document_id = uuid4()
    values = {
        "id": str(uuid4()),
        "job_id": str(uuid4()),
        "document_id": str(document_id),
        "case_id": None,
        "doc_type": "w2",
        "extracted_fields": [make_field(document_id)],
        "annual_income": 85000.00,
        "confidence": "high",
        "notes": None,
        "created_at": datetime(2026, 5, 21, 12, 0, 0),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_get_result_returns_result_response(client, monkeypatch):
    result = make_result()
    monkeypatch.setattr(result_service, "get_result", lambda db, result_id: result)

    response = client.get(f"/results/{result.id}")

    assert response.status_code == 200
    assert response.json()["annual_income"] == 85000.00


def test_get_missing_result_returns_404(client, monkeypatch):
    def raise_not_found(db, result_id):
        raise ResultNotFound("Result not found")

    result_id = uuid4()
    monkeypatch.setattr(result_service, "get_result", raise_not_found)

    response = client.get(f"/results/{result_id}")

    assert response.status_code == 404


def test_get_case_summary_returns_summary(client, monkeypatch):
    case_id = uuid4()
    result = make_result(case_id=str(case_id))
    summary = SimpleNamespace(
        case_id=str(case_id),
        total_annual_income=85000.00,
        results=[result],
        sources=result.extracted_fields,
    )
    monkeypatch.setattr(result_service, "get_case_summary", lambda db, case_id: summary)

    response = client.get(f"/cases/{case_id}/summary")

    assert response.status_code == 200
    assert response.json()["sources"][0]["field"] == "w2_wages"
