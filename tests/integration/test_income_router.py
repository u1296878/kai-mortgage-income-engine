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


def _empty_bucket():
    return {"periods": [], "use_ytd": True}


def _valid_body():
    return {
        "base_pay": {
            "periods": [
                {
                    "date_from": "2026-01-01",
                    "date_through": "2026-04-15",
                    "total_earnings": 17500.0,
                },
                {
                    "date_from": "2025-01-01",
                    "date_through": "2025-12-31",
                    "total_earnings": 60000.0,
                },
            ]
        },
        "overtime": {
            "periods": [
                {
                    "date_from": "2026-01-01",
                    "date_through": "2026-03-31",
                    "total_earnings": 6000.0,
                }
            ],
            "use_ytd": True,
        },
        "bonus": _empty_bucket(),
        "commission": _empty_bucket(),
        "other": _empty_bucket(),
    }


def test_calculate_requires_authentication(client):
    response = client.post("/income/employment/calculate", json=_valid_body())

    assert response.status_code == 401


def test_calculate_returns_total_and_per_bucket_breakdown(client):
    headers, _ = auth_user(client)

    response = client.post(
        "/income/employment/calculate",
        json=_valid_body(),
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["base_pay"]["qualifying_monthly"] == 5000.00
    assert body["overtime"]["qualifying_monthly"] == 2000.00
    assert body["total_monthly"] == 7000.00


def test_calculate_rejects_both_ay_toggles_set(client):
    headers, _ = auth_user(client)
    body = _valid_body()
    body["overtime"]["annualize"] = True
    body["overtime"]["use_ytd"] = True

    response = client.post("/income/employment/calculate", json=body, headers=headers)

    assert response.status_code == 422


def test_calculate_rejects_neither_ay_toggle_set(client):
    headers, _ = auth_user(client)
    body = _valid_body()
    body["overtime"]["use_ytd"] = False

    response = client.post("/income/employment/calculate", json=body, headers=headers)

    assert response.status_code == 422


def test_calculate_rejects_malformed_body(client):
    headers, _ = auth_user(client)

    response = client.post(
        "/income/employment/calculate",
        json={"base_pay": {"periods": "not-a-list"}},
        headers=headers,
    )

    assert response.status_code == 422


def _rental_schedule_e_body():
    return {
        "property_class": "primary_2_4_unit",
        "method": "schedule_e",
        "schedule_e_years": [
            {"months_in_service": 12, "rents_received": 24000, "total_expenses": 10000},
            {"months_in_service": 12, "rents_received": 24000, "total_expenses": 11000},
        ],
    }


def test_rental_calculate_requires_authentication(client):
    response = client.post("/income/rental/calculate", json=_rental_schedule_e_body())

    assert response.status_code == 401


def test_rental_calculate_returns_qualifying_and_breakdown(client):
    headers, _ = auth_user(client)

    response = client.post(
        "/income/rental/calculate",
        json=_rental_schedule_e_body(),
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    # (14000 + 13000) / (12 + 12) = 1125.00
    assert body["qualifying_monthly"] == 1125.00
    assert body["years"][0]["annual_net"] == 14000.0


def test_rental_calculate_rejects_schedule_e_with_no_years(client):
    headers, _ = auth_user(client)
    body = _rental_schedule_e_body()
    body["schedule_e_years"] = []

    response = client.post("/income/rental/calculate", json=body, headers=headers)

    assert response.status_code == 422


def test_rental_calculate_rejects_investment_without_pitia(client):
    headers, _ = auth_user(client)
    body = _rental_schedule_e_body()
    body["property_class"] = "investment"

    response = client.post("/income/rental/calculate", json=body, headers=headers)

    assert response.status_code == 422


def test_rental_calculate_rejects_lease_without_gross_rent(client):
    headers, _ = auth_user(client)
    body = {"property_class": "primary_2_4_unit", "method": "lease"}

    response = client.post("/income/rental/calculate", json=body, headers=headers)

    assert response.status_code == 422
