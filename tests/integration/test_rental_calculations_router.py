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


def _payload(label="123 Main St"):
    return {
        "property_class": "primary_2_4_unit",
        "method": "schedule_e",
        "schedule_e_years": [
            {"months_in_service": 12, "rents_received": 24000, "total_expenses": 10000},
            {"months_in_service": 12, "rents_received": 24000, "total_expenses": 11000},
        ],
        "label": label,
    }


def test_saved_calculation_appears_in_case_summary_total(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()

    created = client.post(
        f"/cases/{case['id']}/rental-calculations",
        json=_payload(),
        headers=headers,
    )
    summary = client.get(f"/cases/{case['id']}/summary", headers=headers)

    assert created.status_code == 200
    # (14000 + 13000) / 24 = 1125.00 monthly; 13500.00 annual
    assert created.json()["qualifying_monthly"] == 1125.00
    assert created.json()["annual_income"] == 13500.00
    assert summary.json()["total_annual_income"] == 13500.00
    assert len(summary.json()["rental_calculations"]) == 1


def test_invalid_investment_without_pitia_returns_422(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    payload = _payload()
    payload["property_class"] = "investment"

    response = client.post(
        f"/cases/{case['id']}/rental-calculations",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422


def test_delete_removes_calculation(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    created = client.post(
        f"/cases/{case['id']}/rental-calculations",
        json=_payload(),
        headers=headers,
    ).json()

    delete = client.delete(
        f"/cases/{case['id']}/rental-calculations/{created['id']}",
        headers=headers,
    )
    fetch = client.get(
        f"/cases/{case['id']}/rental-calculations/{created['id']}",
        headers=headers,
    )

    assert delete.status_code == 204
    assert fetch.status_code == 404


def test_update_included_removes_calculation_from_summary_total(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    created = client.post(
        f"/cases/{case['id']}/rental-calculations",
        json=_payload(),
        headers=headers,
    ).json()

    update = client.patch(
        f"/cases/{case['id']}/rental-calculations/{created['id']}",
        json={"included": False},
        headers=headers,
    )
    summary = client.get(f"/cases/{case['id']}/summary", headers=headers)

    assert update.status_code == 200
    assert update.json()["included"] is False
    assert summary.json()["total_annual_income"] == 0


def test_update_recalculates_rental_calculation(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    created = client.post(
        f"/cases/{case['id']}/rental-calculations",
        json=_payload(),
        headers=headers,
    ).json()
    payload = _payload("Updated")
    payload["schedule_e_years"] = [
        {"months_in_service": 12, "rents_received": 36000, "total_expenses": 12000},
    ]

    update = client.patch(
        f"/cases/{case['id']}/rental-calculations/{created['id']}",
        json=payload,
        headers=headers,
    )

    assert update.status_code == 200
    assert update.json()["label"] == "Updated"
    assert update.json()["annual_income"] == 24000.0
