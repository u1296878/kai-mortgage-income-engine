from uuid import uuid4

from app.models.case import Case
from tests.local_user_helpers import make_user
from app.schemas.extraction import BoundingBox, ExtractedField
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear
from app.schemas.self_employment_results import SelfEmploymentCalculationRequest
from app.services import result_service, schedule_c_se_service
from app.services.self_employment_income_service import run_self_employment_engine


def make_field(field: str, value: float, document_id) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=document_id,
        page=1,
        bounding_box=BoundingBox(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
    )


def test_creates_schedule_c_draft_using_self_employment_engine(test_db):
    case_id = uuid4()
    broker_id = uuid4()
    document_id = uuid4()
    fields = _schedule_c_fields(document_id)
    expected = run_self_employment_engine(_expected_request())

    drafts = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, broker_id, document_id, fields
    )

    assert len(drafts) == 1
    assert drafts[0].kind == "schedule_c"
    assert drafts[0].qualifying_monthly == expected.qualifying_monthly
    assert drafts[0].annual_income == expected.annual_income
    assert drafts[0].included is True
    assert drafts[0].source_document_id == str(document_id)
    assert drafts[0].source_business_key == "business_1"


def test_dedupes_schedule_c_drafts_by_source_document_and_business(test_db):
    case_id = uuid4()
    broker_id = uuid4()
    document_id = uuid4()
    fields = _schedule_c_fields(document_id)

    first = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, broker_id, document_id, fields
    )
    second = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, broker_id, document_id, fields
    )

    assert len(first) == 1
    assert second == []


def test_case_summary_counts_only_included_self_employment_drafts(test_db):
    case_id = uuid4()
    broker_id = uuid4()
    document_id = uuid4()
    local_user = make_user(broker_id)
    test_db.add(Case(id=str(case_id), broker_id=str(broker_id), title="Composite"))
    test_db.commit()
    drafts = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, broker_id, document_id, _schedule_c_fields(document_id)
    )

    included_summary = result_service.get_case_summary(test_db, case_id, local_user)
    drafts[0].included = False
    test_db.commit()
    excluded_summary = result_service.get_case_summary(test_db, case_id, local_user)

    assert included_summary.total_annual_income == drafts[0].annual_income
    assert excluded_summary.total_annual_income == 0.0


def _schedule_c_fields(document_id):
    return [
        make_field("tax_year", 2024.0, document_id),
        make_field("schedule_c_business_1_net_profit", 50000.0, document_id),
        make_field("schedule_c_business_1_nonrecurring_income", 5000.0, document_id),
        make_field("schedule_c_business_1_depletion", 500.0, document_id),
        make_field("schedule_c_business_1_depreciation", 8000.0, document_id),
        make_field("schedule_c_business_1_meals_entertainment_exclusion", 2000.0, document_id),
        make_field("schedule_c_business_1_business_use_of_home", 3000.0, document_id),
        make_field("schedule_c_business_1_business_miles", 1000.0, document_id),
        make_field("schedule_c_business_1_amortization_casualty", 700.0, document_id),
    ]


def _expected_request():
    year = ScheduleCYear(
        tax_year=2024,
        net_profit=50000.0,
        nonrecurring_income=5000.0,
        depletion=500.0,
        depreciation=8000.0,
        meals_entertainment_exclusion=2000.0,
        business_use_of_home=3000.0,
        business_miles=1000.0,
        amortization_casualty=700.0,
    )
    return SelfEmploymentCalculationRequest(
        kind="schedule_c",
        payload=ScheduleCInput(years=[year]).model_dump(mode="json"),
    )
