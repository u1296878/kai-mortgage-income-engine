from uuid import uuid4

from app.models.case import Case
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
    document_id = uuid4()
    fields = _schedule_c_fields(document_id)
    expected = run_self_employment_engine(_expected_request())

    drafts = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, document_id, fields
    )

    assert len(drafts) == 1
    assert drafts[0].kind == "schedule_c"
    assert drafts[0].qualifying_monthly == expected.qualifying_monthly
    assert drafts[0].annual_income == expected.annual_income
    assert drafts[0].included is True
    assert drafts[0].source_document_id == str(document_id)
    assert drafts[0].source_business_key == "schedule_c_single_business"


def test_dedupes_schedule_c_drafts_by_source_document_and_business(test_db):
    case_id = uuid4()
    document_id = uuid4()
    fields = _schedule_c_fields(document_id)

    first = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, document_id, fields
    )
    second = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, document_id, fields
    )

    assert len(first) == 1
    assert second == []


def test_creates_schedule_c_draft_from_model_field_names(test_db):
    case_id = uuid4()
    document_id = uuid4()

    drafts = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, document_id, _model_schedule_c_fields(document_id)
    )

    assert len(drafts) == 1
    assert drafts[0].breakdown["years"][0]["annual_subtotal"] == 102641.0
    assert drafts[0].annual_income == 102641.04
    assert drafts[0].qualifying_monthly == 8553.42


def test_adds_validation_review_flags_to_schedule_c_draft(test_db):
    case_id = uuid4()
    document_id = uuid4()
    review_message = "schedule_c_depreciation may be a missing Schedule C add-back; verify against the form."

    drafts = schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        [
            make_field("tax_year", 2024.0, document_id),
            make_field("schedule_c_net_profit", 85247.0, document_id),
            make_field("schedule_c_business_use_of_home", 3173.0, document_id),
        ],
        [review_message],
    )

    assert len(drafts) == 1
    assert drafts[0].annual_income == 88419.96
    assert drafts[0].breakdown["review_flags"] == [review_message]


def test_case_summary_counts_only_included_self_employment_drafts(test_db):
    case_id = uuid4()
    document_id = uuid4()
    test_db.add(Case(id=str(case_id), title="Composite"))
    test_db.commit()
    drafts = schedule_c_se_service.create_drafts_from_fields(
        test_db, case_id, document_id, _schedule_c_fields(document_id)
    )

    included_summary = result_service.get_case_summary(test_db, case_id)
    drafts[0].included = False
    test_db.commit()
    excluded_summary = result_service.get_case_summary(test_db, case_id)

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


def _model_schedule_c_fields(document_id):
    return [
        make_field("tax_year", 2023.0, document_id),
        make_field("schedule_c_net_profit", 94380.0, document_id),
        make_field("schedule_c_nonrecurring_income", None, document_id),
        make_field("schedule_c_depletion", None, document_id),
        make_field("schedule_c_depreciation", 3633.0, document_id),
        make_field("schedule_c_meals_exclusion", None, document_id),
        make_field("schedule_c_business_use_of_home", 4628.0, document_id),
        make_field("schedule_c_business_miles", 0.0, document_id),
        make_field("schedule_c_amortization_casualty", None, document_id),
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
