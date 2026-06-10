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


def _schedule_c_body():
    return {
        "kind": "schedule_c",
        "payload": {
            "years": [
                {
                    "tax_year": 2025,
                    "net_profit": 50000,
                    "nonrecurring_income": 2000,
                    "depletion": 500,
                    "depreciation": 3000,
                    "meals_entertainment_exclusion": 1000,
                    "business_use_of_home": 1500,
                    "business_miles": 0,
                    "amortization_casualty": 700,
                }
            ]
        },
    }


def _partnership_body():
    return {
        "kind": "partnership",
        "payload": {
            "k1_years": [
                {
                    "ordinary_income": 50000,
                    "net_rental_income": 5000,
                    "guaranteed_payments": 10000,
                }
            ],
            "w2_years": [{"wages": 24000}],
            "form_1065_years": [
                {
                    "passthrough_other_partnerships": 100000,
                    "nonrecurring_income": 5000,
                    "depreciation": 12000,
                    "depreciation_8825": 3000,
                    "depletion": 1000,
                    "amortization_casualty_nonrecurring_loss": 2000,
                    "mortgages_notes_payable_lt_1yr": 10000,
                    "travel_entertainment_exclusion": 1500,
                    "ownership_pct": 0.4,
                }
            ],
        },
    }


def test_self_employment_calculate_returns_personal_schedule_breakdown(client):
    headers, _ = local_user(client)

    response = client.post(
        "/income/self-employment/calculate",
        json=_schedule_c_body(),
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "schedule_c"
    assert body["qualifying_monthly"] == 4391.67
    assert body["annual_income"] == 52700.04
    assert body["breakdown"]["years"][0]["annual_subtotal"] == 52700.0


def test_self_employment_calculate_returns_entity_breakdown(client):
    headers, _ = local_user(client)

    response = client.post(
        "/income/self-employment/calculate",
        json=_partnership_body(),
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "partnership"
    assert body["qualifying_monthly"] == 10800.00
    assert body["breakdown"]["components"][2]["component"] == "form_1065_share"


def test_self_employment_calculate_rejects_unknown_kind(client):
    headers, _ = local_user(client)

    response = client.post(
        "/income/self-employment/calculate",
        json={"kind": "mystery", "payload": {}},
        headers=headers,
    )

    assert response.status_code == 422


def test_self_employment_calculate_rejects_missing_required_field(client):
    headers, _ = local_user(client)
    body = _schedule_c_body()
    del body["payload"]["years"][0]["net_profit"]

    response = client.post(
        "/income/self-employment/calculate",
        json=body,
        headers=headers,
    )

    assert response.status_code == 422
