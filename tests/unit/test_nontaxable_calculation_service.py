from uuid import UUID, uuid4

import pytest

from app.exceptions import CaseNotFound, NonTaxableCalculationNotFound
from app.models.case import Case
from tests.local_user_helpers import make_user
from app.schemas.nontaxable_inputs import (
    NonTaxableCalculationCreate,
    NonTaxableKind,
    NonTaxableMethod,
    NonTaxableSource,
    SocialSecurityMethod,
    SocialSecuritySource,
)
from app.services import nontaxable_calculation_service as service



def make_case(test_db, _unused):
    case = Case(id=str(uuid4()), title="Non-taxable Case")
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
    user = make_user()
    case = make_case(test_db, user.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), income_payload())

    assert calculation.monthly == 2375.0
    assert calculation.annual_income == 28500.0
    assert calculation.kind == "income"
    assert calculation.label == "Child support"


def test_create_persists_social_security_source(test_db):
    user = make_user()
    case = make_case(test_db, user.id)

    calculation = service.create_calculation(
        test_db, UUID(case.id), social_security_payload())

    assert calculation.monthly == 1037.5
    assert calculation.annual_income == 12450.0
    assert calculation.kind == "social_security"


def test_create_on_missing_case_raises_case_not_found(test_db):
    with pytest.raises(CaseNotFound):
        service.create_calculation(test_db, uuid4(), income_payload())


def test_list_returns_case_calculations(test_db):
    user = make_user()
    case = make_case(test_db, user.id)
    service.create_calculation(test_db, UUID(case.id), income_payload("A"))
    service.create_calculation(test_db, UUID(case.id), social_security_payload("B"))

    calculations = service.list_calculations_by_case(test_db, UUID(case.id))

    assert [calc.label for calc in calculations] == ["A", "B"]


def test_get_missing_calculation_raises_not_found(test_db):
    user = make_user()
    case = make_case(test_db, user.id)

    with pytest.raises(NonTaxableCalculationNotFound):
        service.get_calculation(test_db, UUID(case.id), uuid4())


def test_get_calculation_from_other_case_raises_not_found(test_db):
    user = make_user()
    case_one = make_case(test_db, user.id)
    case_two = make_case(test_db, user.id)
    saved = service.create_calculation(test_db, UUID(case_one.id), income_payload())

    with pytest.raises(NonTaxableCalculationNotFound):
        service.get_calculation(test_db, UUID(case_two.id), UUID(saved.id))


def test_delete_removes_calculation(test_db):
    user = make_user()
    case = make_case(test_db, user.id)
    saved = service.create_calculation(test_db, UUID(case.id), income_payload())

    service.delete_calculation(test_db, UUID(case.id), UUID(saved.id))

    assert service.list_calculations_by_case(test_db, UUID(case.id)) == []
