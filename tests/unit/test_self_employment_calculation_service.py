from uuid import UUID, uuid4

import pytest

from app.exceptions import CaseNotFound, SelfEmploymentCalculationNotFound
from app.models.case import Case
from tests.local_user_helpers import make_user
from app.schemas.self_employment_results import (
    SelfEmploymentCalculationCreate,
    SelfEmploymentCalculationUpdate,
)
from app.services import self_employment_calculation_service as service



def make_case(test_db, broker_id):
    case = Case(id=str(uuid4()), broker_id=str(broker_id), title="Self-employed Case")
    test_db.add(case)
    test_db.commit()
    return case


def schedule_d_payload(label="Capital gains"):
    return SelfEmploymentCalculationCreate(
        kind="schedule_d",
        label=label,
        payload={"years": [{"recurring_capital_gains": 24000}]},
    )


def partnership_payload(label="Partnership"):
    return SelfEmploymentCalculationCreate(
        kind="partnership",
        label=label,
        payload={
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
    )


def test_create_persists_personal_schedule(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), schedule_d_payload(), broker
    )

    assert calculation.kind == "schedule_d"
    assert calculation.qualifying_monthly == 2000.0
    assert calculation.annual_income == 24000.0
    assert calculation.broker_id == broker.id


def test_create_persists_entity_calculation(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), partnership_payload(), broker
    )

    assert calculation.kind == "partnership"
    assert calculation.qualifying_monthly == 10800.0
    assert calculation.annual_income == 129600.0
    assert calculation.label == "Partnership"


def test_create_on_other_brokers_case_raises_case_not_found(test_db):
    owner = make_user()
    intruder = make_user()
    case = make_case(test_db, owner.id)

    with pytest.raises(CaseNotFound):
        service.create_calculation(test_db, UUID(case.id), schedule_d_payload(), intruder)


def test_list_returns_case_calculations(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)
    service.create_calculation(test_db, UUID(case.id), schedule_d_payload("A"), broker)
    service.create_calculation(test_db, UUID(case.id), partnership_payload("B"), broker)

    calculations = service.list_calculations_by_case(test_db, UUID(case.id), broker)

    assert [calc.label for calc in calculations] == ["A", "B"]


def test_update_calculation_sets_included(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)
    saved = service.create_calculation(test_db, UUID(case.id), schedule_d_payload(), broker)

    updated = service.update_calculation(
        test_db,
        UUID(case.id),
        UUID(saved.id),
        SelfEmploymentCalculationUpdate(included=False),
        broker,
    )

    assert updated.included is False


def test_get_missing_calculation_raises_not_found(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    with pytest.raises(SelfEmploymentCalculationNotFound):
        service.get_calculation(test_db, UUID(case.id), uuid4(), broker)


def test_get_calculation_from_other_case_raises_not_found(test_db):
    broker = make_user()
    case_one = make_case(test_db, broker.id)
    case_two = make_case(test_db, broker.id)
    saved = service.create_calculation(
        test_db, UUID(case_one.id), schedule_d_payload(), broker
    )

    with pytest.raises(SelfEmploymentCalculationNotFound):
        service.get_calculation(test_db, UUID(case_two.id), UUID(saved.id), broker)


def test_delete_removes_calculation(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)
    saved = service.create_calculation(test_db, UUID(case.id), schedule_d_payload(), broker)

    service.delete_calculation(test_db, UUID(case.id), UUID(saved.id), broker)

    assert service.list_calculations_by_case(test_db, UUID(case.id), broker) == []
