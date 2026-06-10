import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from tests.local_user_helpers import local_user


@pytest.fixture
def client(test_db):
    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _payload(label="Child support"):
    return {
        "kind": "income",
        "income": {
            "method": "total_adjusted",
            "annual_gross": 24000,
            "annual_taxable": 6000,
        },
        "label": label,
    }


def test_saved_calculation_appears_in_case_summary_total(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()

    created = client.post(
        f"/cases/{case['id']}/nontaxable-calculations",
        json=_payload(),
        headers=headers,
    )
    summary = client.get(f"/cases/{case['id']}/summary", headers=headers)

    assert created.status_code == 200
    assert created.json()["monthly"] == 2375.0
    assert created.json()["annual_income"] == 28500.0
    assert summary.json()["total_annual_income"] == 28500.0
    assert len(summary.json()["nontaxable_calculations"]) == 1


def test_invalid_missing_declared_source_returns_422(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()

    response = client.post(
        f"/cases/{case['id']}/nontaxable-calculations",
        json={"kind": "income", "social_security": {"method": "gross_100"}},
        headers=headers,
    )

    assert response.status_code == 422


def test_delete_removes_calculation(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    created = client.post(
        f"/cases/{case['id']}/nontaxable-calculations",
        json=_payload(),
        headers=headers,
    ).json()

    delete = client.delete(
        f"/cases/{case['id']}/nontaxable-calculations/{created['id']}",
        headers=headers,
    )
    fetch = client.get(
        f"/cases/{case['id']}/nontaxable-calculations/{created['id']}",
        headers=headers,
    )

    assert delete.status_code == 204
    assert fetch.status_code == 404
