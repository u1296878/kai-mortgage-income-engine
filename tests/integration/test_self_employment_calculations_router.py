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


def _payload(label="Capital gains"):
    return {
        "kind": "schedule_d",
        "label": label,
        "payload": {"years": [{"recurring_capital_gains": 24000}]},
    }


def test_saved_calculation_appears_in_case_summary_total(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()

    created = client.post(
        f"/cases/{case['id']}/self-employment-calculations",
        json=_payload(),
        headers=headers,
    )
    summary = client.get(f"/cases/{case['id']}/summary", headers=headers)

    assert created.status_code == 200
    assert created.json()["qualifying_monthly"] == 2000.0
    assert created.json()["annual_income"] == 24000.0
    assert summary.json()["total_annual_income"] == 24000.0
    assert len(summary.json()["self_employment_calculations"]) == 1


def test_update_included_excludes_from_case_summary(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    created = client.post(
        f"/cases/{case['id']}/self-employment-calculations",
        json=_payload(),
        headers=headers,
    ).json()

    update = client.patch(
        f"/cases/{case['id']}/self-employment-calculations/{created['id']}",
        json={"included": False},
        headers=headers,
    )
    summary = client.get(f"/cases/{case['id']}/summary", headers=headers)

    assert update.status_code == 200
    assert update.json()["included"] is False
    assert summary.json()["total_annual_income"] == 0.0


def test_delete_removes_calculation(client):
    headers, _ = local_user(client)
    case = client.post("/cases", json={"title": "Case"}, headers=headers).json()
    created = client.post(
        f"/cases/{case['id']}/self-employment-calculations",
        json=_payload(),
        headers=headers,
    ).json()

    delete = client.delete(
        f"/cases/{case['id']}/self-employment-calculations/{created['id']}",
        headers=headers,
    )
    fetch = client.get(
        f"/cases/{case['id']}/self-employment-calculations/{created['id']}",
        headers=headers,
    )

    assert delete.status_code == 204
    assert fetch.status_code == 404
