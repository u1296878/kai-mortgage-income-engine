from uuid import UUID, uuid4

import pytest

from app.exceptions import CaseNotFound, RentalCalculationNotFound
from app.models.case import Case
from tests.local_user_helpers import make_user
from app.schemas.rental_inputs import (
    PropertyClass,
    RentalMethod,
    RentalProperty,
    ScheduleEYear,
)
from app.services import rental_calculation_service as service



def make_case(test_db, broker_id):
    case = Case(id=str(uuid4()), broker_id=str(broker_id), title="Rental Case")
    test_db.add(case)
    test_db.commit()
    return case


def primary_property():
    return RentalProperty(
        property_class=PropertyClass.primary_2_4_unit,
        method=RentalMethod.schedule_e,
        schedule_e_years=[
            ScheduleEYear(months_in_service=12, rents_received=24000, total_expenses=10000),
            ScheduleEYear(months_in_service=12, rents_received=24000, total_expenses=11000),
        ],
    )


def loss_property():
    return RentalProperty(
        property_class=PropertyClass.primary_2_4_unit,
        method=RentalMethod.schedule_e,
        schedule_e_years=[
            ScheduleEYear(months_in_service=12, rents_received=12000, total_expenses=30000),
        ],
    )


def test_create_persists_computed_totals(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), primary_property(), None, "123 Main St", broker
    )

    # (14000 + 13000) / 24 = 1125.00
    assert calculation.qualifying_monthly == 1125.00
    assert calculation.annual_income == 13500.00
    assert calculation.label == "123 Main St"
    assert calculation.broker_id == broker.id
    assert calculation.breakdown["years"][0]["annual_net"] == 14000.0


def test_create_loss_persists_negative_annual_income(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), loss_property(), None, None, broker
    )

    # -18000 / 12 = -1500 monthly; -18000 annual (not clamped)
    assert calculation.qualifying_monthly == -1500.00
    assert calculation.annual_income == -18000.00


def test_create_on_other_brokers_case_raises_case_not_found(test_db):
    owner = make_user()
    intruder = make_user()
    case = make_case(test_db, owner.id)

    with pytest.raises(CaseNotFound):
        service.create_calculation(
            test_db, UUID(case.id), primary_property(), None, None, intruder
        )


def test_list_returns_case_calculations(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)
    service.create_calculation(test_db, UUID(case.id), primary_property(), None, "A", broker)
    service.create_calculation(test_db, UUID(case.id), primary_property(), None, "B", broker)

    calculations = service.list_calculations_by_case(test_db, UUID(case.id), broker)

    assert [calc.label for calc in calculations] == ["A", "B"]


def test_get_returns_calculation(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)
    saved = service.create_calculation(
        test_db, UUID(case.id), primary_property(), None, "A", broker
    )

    fetched = service.get_calculation(test_db, UUID(case.id), UUID(saved.id), broker)

    assert fetched.id == saved.id


def test_get_missing_calculation_raises_not_found(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    with pytest.raises(RentalCalculationNotFound):
        service.get_calculation(test_db, UUID(case.id), uuid4(), broker)


def test_get_calculation_from_other_case_raises_not_found(test_db):
    broker = make_user()
    case_one = make_case(test_db, broker.id)
    case_two = make_case(test_db, broker.id)
    saved = service.create_calculation(
        test_db, UUID(case_one.id), primary_property(), None, "A", broker
    )

    with pytest.raises(RentalCalculationNotFound):
        service.get_calculation(test_db, UUID(case_two.id), UUID(saved.id), broker)


def test_delete_removes_calculation(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)
    saved = service.create_calculation(
        test_db, UUID(case.id), primary_property(), None, "A", broker
    )

    service.delete_calculation(test_db, UUID(case.id), UUID(saved.id), broker)

    assert service.list_calculations_by_case(test_db, UUID(case.id), broker) == []
