from uuid import uuid4

from app.models.case import Case
from app.repositories import employment_calculation_repo
from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import employment_paystub_service, employment_w2_service


def test_standalone_paystub_creates_ytd_employment_draft(test_db):
    case_id = _case(test_db)
    document_id = uuid4()

    drafts = employment_paystub_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        _paystub_fields(document_id, 45000.0, "2025-06-30", "Acme Corp"),
    )

    assert len(drafts) == 1
    assert drafts[0].label == "Pay stub - Acme Corp"
    assert drafts[0].total_monthly == 7500.0
    assert drafts[0].annual_income == 90000.0


def test_paystub_merges_with_same_employer_w2(test_db):
    case_id = _case(test_db)
    w2_document_id = uuid4()
    paystub_document_id = uuid4()

    employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        w2_document_id,
        [_field("tax_year", 2024.0, w2_document_id), _field("w2_wages", 84000.0, w2_document_id), _field("w2_employer_name", 0.0, w2_document_id, "Acme Corp")],
    )
    drafts = employment_paystub_service.create_drafts_from_fields(
        test_db,
        case_id,
        paystub_document_id,
        _paystub_fields(paystub_document_id, 45000.0, "2025-06-30", "Acme Corp"),
    )
    calculations = employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(drafts) == 1
    assert len(calculations) == 1
    assert calculations[0].total_monthly == 7166.67
    assert calculations[0].annual_income == 86000.0
    assert len(calculations[0].inputs["base_pay"]["periods"]) == 2


def test_paystub_different_employer_stays_separate(test_db):
    case_id = _case(test_db)
    w2_document_id = uuid4()
    paystub_document_id = uuid4()

    employment_w2_service.create_drafts_from_fields(
        test_db,
        case_id,
        w2_document_id,
        [_field("tax_year", 2024.0, w2_document_id), _field("w2_wages", 84000.0, w2_document_id), _field("w2_employer_name", 0.0, w2_document_id, "Acme Corp")],
    )
    employment_paystub_service.create_drafts_from_fields(
        test_db,
        case_id,
        paystub_document_id,
        _paystub_fields(paystub_document_id, 45000.0, "2025-06-30", "Other LLC"),
    )

    assert len(employment_calculation_repo.list_by_case(test_db, case_id)) == 2


def test_missing_paystub_ytd_creates_no_draft(test_db):
    case_id = _case(test_db)
    document_id = uuid4()

    drafts = employment_paystub_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        [_field("paystub_period_end", None, document_id, "2025-06-30")],
    )

    assert drafts == []


def test_bad_paystub_period_end_creates_no_draft(test_db):
    case_id = _case(test_db)
    document_id = uuid4()

    drafts = employment_paystub_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        _paystub_fields(document_id, 45000.0, "not a date", "Acme Corp"),
    )

    assert drafts == []


def test_parse_period_end_accepts_common_formats():
    assert str(employment_paystub_service.parse_period_end("2025-06-30")) == "2025-06-30"
    assert str(employment_paystub_service.parse_period_end("6/30/2025")) == "2025-06-30"


def _case(test_db):
    case_id = uuid4()
    test_db.add(Case(id=str(case_id), title="Paystub Case"))
    test_db.commit()
    return case_id


def _paystub_fields(document_id, gross_ytd, period_end, employer):
    return [
        _field("paystub_gross_ytd", gross_ytd, document_id),
        _field("paystub_period_end", None, document_id, period_end),
        _field("paystub_employer_name", 0.0, document_id, employer),
    ]


def _field(field, value, document_id, raw_text=None):
    return ExtractedField(
        field=field,
        value=value,
        raw_text=raw_text,
        document_id=document_id,
        page=1,
        bounding_box=BoundingBox(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
    )
