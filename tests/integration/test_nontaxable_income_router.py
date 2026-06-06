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


def _income_body():
    return {
        "kind": "income",
        "income": {
            "method": "total_adjusted",
            "annual_gross": 24000,
            "annual_taxable": 6000,
        },
    }


def _social_security_body():
    return {
        "kind": "social_security",
        "social_security": {"method": "adjusted", "annual_gross": 12000},
    }


def test_nontaxable_calculate_requires_authentication(client):
    response = client.post("/income/nontaxable/calculate", json=_income_body())

    assert response.status_code == 401


def test_nontaxable_calculate_returns_income_source_result(client):
    headers, _ = auth_user(client)

    response = client.post(
        "/income/nontaxable/calculate",
        json=_income_body(),
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["monthly"] == 2375.0
    assert body["method"] == "total_adjusted"


def test_nontaxable_calculate_returns_social_security_result(client):
    headers, _ = auth_user(client)

    response = client.post(
        "/income/nontaxable/calculate",
        json=_social_security_body(),
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["monthly"] == 1037.5
    assert body["eligible_monthly"] == 37.5


def test_nontaxable_calculate_rejects_missing_declared_kind_source(client):
    headers, _ = auth_user(client)

    response = client.post(
        "/income/nontaxable/calculate",
        json={"kind": "income", "social_security": {"method": "gross_100"}},
        headers=headers,
    )

    assert response.status_code == 422
