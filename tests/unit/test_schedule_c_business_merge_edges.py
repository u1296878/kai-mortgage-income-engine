from uuid import uuid4

from app.repositories import self_employment_calculation_repo
from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import schedule_c_se_service
from app.services.schedule_c_business_match import REVIEW_UNMATCHED_BUSINESS


def make_field(
    field: str,
    value: float | None,
    document_id,
    raw_text: str | None = None,
) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=document_id,
        page=1,
        bounding_box=BoundingBox(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
        raw_text=raw_text,
    )


def test_unnamed_single_business_merges_when_later_year_has_name(test_db):
    case_id = uuid4()
    doc_2023 = uuid4()
    doc_2024 = uuid4()

    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2023,
        _fields(doc_2023, 2023, 12000.0),
    )
    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2024,
        _fields(doc_2024, 2024, 24000.0, "Law Office of David S. Hendrickson"),
    )

    calculations = self_employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(calculations) == 1
    assert calculations[0].qualifying_monthly == 1500.0
    assert calculations[0].source_business_key == "schedule_c_name:law office of david s hendrickson"


def test_named_single_business_merges_when_later_year_loses_name(test_db):
    case_id = uuid4()
    doc_2023 = uuid4()
    doc_2024 = uuid4()

    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2023,
        _fields(doc_2023, 2023, 12000.0, "Law Office of David S. Hendrickson"),
    )
    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2024,
        _fields(doc_2024, 2024, 24000.0),
    )

    calculations = self_employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(calculations) == 1
    assert calculations[0].qualifying_monthly == 1500.0
    assert calculations[0].source_business_key == "schedule_c_name:law office of david s hendrickson"


def test_unmatched_cross_year_business_is_flagged_for_review(test_db):
    case_id = uuid4()
    doc_2023 = uuid4()
    doc_2024 = uuid4()

    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2023,
        _fields(doc_2023, 2023, 12000.0, "Johnson Plumbing"),
    )
    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2024,
        _fields(doc_2024, 2024, 24000.0, "Hendrickson Law"),
    )

    calculations = self_employment_calculation_repo.list_by_case(test_db, case_id)
    review_flags = calculations[1].breakdown["review_flags"]

    assert len(calculations) == 2
    assert REVIEW_UNMATCHED_BUSINESS in review_flags


def test_single_prior_business_does_not_match_multiple_later_businesses(test_db):
    case_id = uuid4()
    doc_2023 = uuid4()
    doc_2024 = uuid4()

    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2023,
        _fields(doc_2023, 2023, 12000.0),
    )
    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2024,
        [
            make_field("tax_year", 2024.0, doc_2024),
            make_field("schedule_c_business_1_business_name", 0.0, doc_2024, "Alpha Consulting"),
            make_field("schedule_c_business_1_net_profit", 24000.0, doc_2024),
            make_field("schedule_c_business_2_business_name", 0.0, doc_2024, "Beta Repair"),
            make_field("schedule_c_business_2_net_profit", 36000.0, doc_2024),
        ],
    )

    calculations = self_employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(calculations) == 3
    assert calculations[1].breakdown["review_flags"] == [REVIEW_UNMATCHED_BUSINESS]


def _fields(
    document_id,
    tax_year: int,
    net_profit: float,
    business_name: str | None = None,
) -> list[ExtractedField]:
    fields = [
        make_field("tax_year", float(tax_year), document_id),
        make_field("schedule_c_business_1_net_profit", net_profit, document_id),
    ]
    if business_name:
        fields.append(
            make_field("schedule_c_business_1_business_name", 0.0, document_id, business_name)
        )
    return fields
