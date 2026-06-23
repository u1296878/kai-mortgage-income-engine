from uuid import uuid4

from app.models.case import Case
from app.repositories import employment_calculation_repo
from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import employment_w2_service, result_service


def test_one_w2_creates_full_year_employment_draft(test_db):
    case_id = _case(test_db)
    document_id = uuid4()

    drafts = employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        _w2_fields(document_id, 2023, 85000.0, "Acme Corp"),
    )

    assert len(drafts) == 1
    assert drafts[0].label == "W-2 - Acme Corp"
    assert drafts[0].total_monthly == 7083.33
    assert drafts[0].annual_income == 85000.0
    assert drafts[0].included is True
    assert drafts[0].source_document_id == str(document_id)
    assert drafts[0].source_employer_key == "employer:acme corp"


def test_two_w2s_for_same_employer_merge_to_two_year_average(test_db):
    case_id = _case(test_db)
    first_document_id = uuid4()
    second_document_id = uuid4()

    employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        first_document_id,
        _w2_fields(first_document_id, 2023, 85000.0, "Acme Corp"),
    )
    drafts = employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        second_document_id,
        _w2_fields(second_document_id, 2024, 90000.0, "Acme Corp"),
    )
    calculations = employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(drafts) == 1
    assert len(calculations) == 1
    assert calculations[0].total_monthly == 7291.67
    assert calculations[0].annual_income == 87500.0
    assert len(calculations[0].inputs["base_pay"]["periods"]) == 2


def test_two_w2s_for_different_employers_stay_separate(test_db):
    case_id = _case(test_db)
    first_document_id = uuid4()
    second_document_id = uuid4()

    employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        first_document_id,
        _w2_fields(first_document_id, 2023, 85000.0, "Acme Corp"),
    )
    employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        second_document_id,
        _w2_fields(second_document_id, 2024, 90000.0, "Other LLC"),
    )
    calculations = employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(calculations) == 2
    assert sum(calc.annual_income for calc in calculations) == 175000.0


def test_missing_w2_wages_creates_no_draft(test_db):
    case_id = _case(test_db)
    document_id = uuid4()

    drafts = employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        [_field("tax_year", 2023.0, document_id)],
    )

    assert drafts == []
    assert employment_calculation_repo.list_by_case(test_db, case_id) == []


def test_w2_review_flags_are_carried_to_breakdown(test_db):
    case_id = _case(test_db)
    document_id = uuid4()
    review_message = "W-2 Box 2 federal withholding exceeds Box 1 wages."

    drafts = employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        _w2_fields(document_id, 2023, 85000.0, None),
        [review_message],
    )

    assert set(drafts[0].breakdown["review_flags"]) == {
        employment_w2_service.MISSING_EMPLOYER_FLAG,
        review_message,
    }


def test_case_summary_counts_only_included_w2_employment_drafts(test_db):
    case_id = _case(test_db)
    document_id = uuid4()
    drafts = employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        _w2_fields(document_id, 2023, 85000.0, "Acme Corp"),
    )

    included_summary = result_service.get_case_summary(test_db, case_id)
    drafts[0].included = False
    test_db.commit()
    excluded_summary = result_service.get_case_summary(test_db, case_id)

    assert included_summary.total_annual_income == 85000.0
    assert excluded_summary.total_annual_income == 0.0


def _case(test_db):
    case_id = uuid4()
    test_db.add(Case(id=str(case_id), title="W-2 Case"))
    test_db.commit()
    return case_id


def _w2_fields(document_id, tax_year, wages, employer):
    fields = [_field("tax_year", float(tax_year), document_id), _field("w2_wages", wages, document_id)]
    if employer:
        fields.append(_field("w2_employer_name", 0.0, document_id, employer))
    return fields


def _field(field, value, document_id, raw_text=None):
    return ExtractedField(
        field=field,
        value=value,
        raw_text=raw_text,
        document_id=document_id,
        page=1,
        bounding_box=BoundingBox(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
    )
