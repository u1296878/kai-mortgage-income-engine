from uuid import UUID, uuid4

import pytest

from app.exceptions import CaseNotFound, NonTaxableCalculationNotFound
from app.models.case import Case
from app.models.user import User
from app.schemas.nontaxable_inputs import (
    NonTaxableCalculationCreate,
    NonTaxableKind,
    NonTaxableMethod,
    NonTaxableSource,
    SocialSecurityMethod,
    SocialSecuritySource,
)
from app.services import nontaxable_calculation_service as service


def make_user(user_id=None, role="broker"):
    return User(
        id=str(user_id or uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="hash",
        role=role,
    )


def make_case(test_db, broker_id):
    case = Case(id=str(uuid4()), broker_id=str(broker_id), title="Non-taxable Case")
    test_db.add(case)
    test_db.commit()
    return case


def income_payload(label="Child support"):
    return NonTaxableCalculationCreate(
        kind=NonTaxableKind.income,
        income=NonTaxableSource(
            method=NonTaxableMethod.total_adjusted,
            annual_gross=24000,
            annual_taxable=6000,
        ),
        label=label,
    )


def social_security_payload(label="SSI"):
    return NonTaxableCalculationCreate(
        kind=NonTaxableKind.social_security,
        social_security=SocialSecuritySource(
            method=SocialSecurityMethod.adjusted,
            annual_gross=12000,
        ),
        label=label,
    )


def test_create_persists_income_source(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), income_payload(), broker
    )

    assert calculation.monthly == 2375.0
    assert calculation.annual_income == 28500.0
    assert calculation.kind == "income"
    assert calculation.label == "Child support"
    assert calculation.broker_id == broker.id


def test_create_persists_social_security_source(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), social_security_payload(), broker
    )

    assert calculation.monthly == 1037.5
    assert calculation.annual_income == 12450.0
    assert calculation.kind == "social_security"


def test_create_on_other_brokers_case_raises_case_not_found(test_db):
    owner = make_user()
    intruder = make_user()
    case = make_case(test_db, owner.id)

    with pytest.raises(CaseNotFound):
        service.create_calculation(test_db, UUID(case.id), income_payload(), intruder)


def test_manager_can_create_for_any_case(test_db):
    broker = make_user()
    manager = make_user(role="manager")
    case = make_case(test_db, broker.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), income_payload(), manager
    )

    assert calculation.case_id == case.id


def test_list_returns_case_calculations(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)
    service.create_calculation(test_db, UUID(case.id), income_payload("A"), broker)
    service.create_calculation(test_db, UUID(case.id), social_security_payload("B"), broker)

    calculations = service.list_calculations_by_case(test_db, UUID(case.id), broker)

    assert [calc.label for calc in calculations] == ["A", "B"]


def test_get_missing_calculation_raises_not_found(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)

    with pytest.raises(NonTaxableCalculationNotFound):
        service.get_calculation(test_db, UUID(case.id), uuid4(), broker)


def test_get_calculation_from_other_case_raises_not_found(test_db):
    broker = make_user()
    case_one = make_case(test_db, broker.id)
    case_two = make_case(test_db, broker.id)
    saved = service.create_calculation(test_db, UUID(case_one.id), income_payload(), broker)

    with pytest.raises(NonTaxableCalculationNotFound):
        service.get_calculation(test_db, UUID(case_two.id), UUID(saved.id), broker)


def test_delete_removes_calculation(test_db):
    broker = make_user()
    case = make_case(test_db, broker.id)
    saved = service.create_calculation(test_db, UUID(case.id), income_payload(), broker)

    service.delete_calculation(test_db, UUID(case.id), UUID(saved.id), broker)

    assert service.list_calculations_by_case(test_db, UUID(case.id), broker) == []
