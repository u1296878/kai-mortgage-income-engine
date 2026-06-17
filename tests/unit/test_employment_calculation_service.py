from datetime import date
from uuid import UUID, uuid4

import pytest

from app.exceptions import CaseNotFound, EmploymentCalculationNotFound
from app.models.case import Case
from tests.local_user_helpers import make_user
from app.schemas.income_inputs import (
    BasePay,
    EmploymentInput,
    EmploymentPeriod,
    VariableBucket,
)
from app.services import employment_calculation_service as service



def make_case(test_db, _unused):
    case = Case(id=str(uuid4()), title="Smith Purchase")
    test_db.add(case)
    test_db.commit()
    return case


def empty_bucket():
    return VariableBucket(periods=[], use_ytd=True)


def employment_input():
    base = BasePay(
        periods=[
            EmploymentPeriod(
                date_from=date(2026, 1, 1),
                date_through=date(2026, 4, 15),
                total_earnings=17500.0,
            ),
            EmploymentPeriod(
                date_from=date(2025, 1, 1),
                date_through=date(2025, 12, 31),
                total_earnings=60000.0,
            ),
        ]
    )
    overtime = VariableBucket(
        periods=[
            EmploymentPeriod(
                date_from=date(2026, 1, 1),
                date_through=date(2026, 3, 31),
                total_earnings=6000.0,
            )
        ],
        use_ytd=True,
    )
    return EmploymentInput(
        base_pay=base,
        overtime=overtime,
        bonus=empty_bucket(),
        commission=empty_bucket(),
        other=empty_bucket(),
    )


def test_create_persists_computed_totals(test_db):
    user = make_user()
    case = make_case(test_db, user.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), employment_input(), None, "Acme Corp")

    assert calculation.total_monthly == 7000.00
    assert calculation.annual_income == 84000.00
    assert calculation.label == "Acme Corp"
    assert calculation.breakdown["base_pay"]["qualifying_monthly"] == 5000.00


def test_create_stores_inputs_snapshot(test_db):
    user = make_user()
    case = make_case(test_db, user.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), employment_input(), None, None)

    assert calculation.inputs["overtime"]["use_ytd"] is True
    assert calculation.inputs["base_pay"]["periods"][0]["total_earnings"] == 17500.0


def test_create_on_missing_case_raises_case_not_found(test_db):
    with pytest.raises(CaseNotFound):
        service.create_calculation(
            test_db, uuid4(), employment_input(), None, None)


def test_list_returns_case_calculations(test_db):
    user = make_user()
    case = make_case(test_db, user.id)
    service.create_calculation(test_db, UUID(case.id), employment_input(), None, "A")
    service.create_calculation(test_db, UUID(case.id), employment_input(), None, "B")

    calculations = service.list_calculations_by_case(test_db, UUID(case.id))

    assert [calc.label for calc in calculations] == ["A", "B"]


def test_get_returns_calculation(test_db):
    user = make_user()
    case = make_case(test_db, user.id)
    saved = service.create_calculation(
        test_db, UUID(case.id), employment_input(), None, "A")

    fetched = service.get_calculation(test_db, UUID(case.id), UUID(saved.id))

    assert fetched.id == saved.id


def test_get_missing_calculation_raises_not_found(test_db):
    user = make_user()
    case = make_case(test_db, user.id)

    with pytest.raises(EmploymentCalculationNotFound):
        service.get_calculation(test_db, UUID(case.id), uuid4())


def test_get_calculation_from_other_case_raises_not_found(test_db):
    user = make_user()
    case_one = make_case(test_db, user.id)
    case_two = make_case(test_db, user.id)
    saved = service.create_calculation(
        test_db, UUID(case_one.id), employment_input(), None, "A")

    with pytest.raises(EmploymentCalculationNotFound):
        service.get_calculation(test_db, UUID(case_two.id), UUID(saved.id))


def test_delete_removes_calculation(test_db):
    user = make_user()
    case = make_case(test_db, user.id)
    saved = service.create_calculation(
        test_db, UUID(case.id), employment_input(), None, "A")

    service.delete_calculation(test_db, UUID(case.id), UUID(saved.id))

    assert service.list_calculations_by_case(test_db, UUID(case.id)) == []
