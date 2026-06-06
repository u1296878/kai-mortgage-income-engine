import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from tests.auth_helpers import auth_user


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


def test_create_requires_authentication(client):
    case_id = "11111111-1111-1111-1111-111111111111"

    response = client.post(f"/cases/{case_id}/nontaxable-calculations", json=_payload())

    assert response.status_code == 401


def test_saved_calculation_appears_in_case_summary_total(client):
    headers, _ = auth_user(client)
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
    headers, _ = auth_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()

    response = client.post(
        f"/cases/{case['id']}/nontaxable-calculations",
        json={"kind": "income", "social_security": {"method": "gross_100"}},
        headers=headers,
    )

    assert response.status_code == 422


def test_broker_cannot_create_for_other_brokers_case(client):
    headers_a, _ = auth_user(client)
    headers_b, _ = auth_user(client)
    case_b = client.post("/cases", json={"title": "B"}, headers=headers_b).json()

    response = client.post(
        f"/cases/{case_b['id']}/nontaxable-calculations",
        json=_payload(),
        headers=headers_a,
    )

    assert response.status_code == 404


def test_list_is_scoped_to_case_owner(client):
    headers_a, _ = auth_user(client)
    headers_b, _ = auth_user(client)
    case_a = client.post("/cases", json={"title": "A"}, headers=headers_a).json()
    client.post(
        f"/cases/{case_a['id']}/nontaxable-calculations",
        json=_payload(),
        headers=headers_a,
    )

    own = client.get(f"/cases/{case_a['id']}/nontaxable-calculations", headers=headers_a)
    other = client.get(f"/cases/{case_a['id']}/nontaxable-calculations", headers=headers_b)

    assert own.status_code == 200
    assert [calc["label"] for calc in own.json()] == ["Child support"]
    assert other.status_code == 404


def test_delete_removes_calculation(client):
    headers, _ = auth_user(client)
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
