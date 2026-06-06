from uuid import uuid4

from app.models.case import Case
from app.models.employment_calculation import EmploymentCalculation
from app.models.nontaxable_calculation import NonTaxableCalculation
from app.models.rental_calculation import RentalCalculation
from app.models.user import User
from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import result_service


def make_user(role="broker"):
    return User(
        id=str(uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="hash",
        role=role,
    )


def make_field(field: str = "w2_wages", value: float = 85000.00) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
    )


def test_summary_adds_saved_employment_calculations(test_db):
    case_id, broker_id, manager = _case_with_result(test_db, 85000.00)
    test_db.add(_employment_calc(case_id, broker_id, 84000.00))
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, manager)

    assert summary.total_annual_income == 169000.00
    assert len(summary.employment_calculations) == 1


def test_summary_adds_saved_rental_calculations(test_db):
    case_id, broker_id, manager = _case_with_result(test_db, 85000.00)
    test_db.add(_rental_calc(case_id, broker_id, 12000.00))
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, manager)

    assert summary.total_annual_income == 97000.00
    assert len(summary.rental_calculations) == 1


def test_summary_negative_rental_calculation_reduces_total(test_db):
    case_id, broker_id, manager = _case_with_result(test_db, 85000.00)
    test_db.add(_rental_calc(case_id, broker_id, -18000.00))
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, manager)

    assert summary.total_annual_income == 67000.00


def test_summary_adds_saved_nontaxable_calculations(test_db):
    case_id, broker_id, manager = _case_with_result(test_db, 85000.00)
    test_db.add(_nontaxable_calc(case_id, broker_id, 12450.00))
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, manager)

    assert summary.total_annual_income == 97450.00
    assert len(summary.nontaxable_calculations) == 1


def _case_with_result(test_db, annual_income):
    case_id = uuid4()
    broker_id = uuid4()
    manager = make_user(role="manager")
    test_db.add(Case(id=str(case_id), broker_id=str(broker_id), title="Add-on"))
    test_db.commit()
    result_service.save_extraction_result(
        test_db, uuid4(), uuid4(), case_id, "w2", [make_field(value=annual_income)]
    )
    return case_id, broker_id, manager


def _employment_calc(case_id, broker_id, annual_income):
    monthly = round(annual_income / 12, 2)
    bucket = {"qualifying_monthly": 0.0, "rate_of_pay_monthly": 0.0, "periods": []}
    breakdown = {
        "base_pay": {**bucket, "qualifying_monthly": monthly},
        "overtime": bucket,
        "bonus": bucket,
        "commission": bucket,
        "other": bucket,
        "total_monthly": monthly,
    }
    return EmploymentCalculation(
        case_id=str(case_id),
        broker_id=str(broker_id),
        label="Acme Corp",
        inputs={},
        total_monthly=monthly,
        annual_income=annual_income,
        breakdown=breakdown,
    )


def _rental_calc(case_id, broker_id, annual_income):
    monthly = round(annual_income / 12, 2)
    return RentalCalculation(
        case_id=str(case_id),
        broker_id=str(broker_id),
        label="123 Main St",
        inputs={},
        qualifying_monthly=monthly,
        annual_income=annual_income,
        breakdown={
            "qualifying_monthly": monthly,
            "property_class": "primary_2_4_unit",
            "method": "schedule_e",
            "years": [],
        },
    )


def _nontaxable_calc(case_id, broker_id, annual_income):
    monthly = round(annual_income / 12, 2)
    return NonTaxableCalculation(
        case_id=str(case_id),
        broker_id=str(broker_id),
        label="SSI",
        kind="social_security",
        inputs={},
        monthly=monthly,
        annual_income=annual_income,
        breakdown={"monthly": monthly, "method": "adjusted"},
    )
