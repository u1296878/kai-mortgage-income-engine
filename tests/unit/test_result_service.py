from uuid import uuid4

from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import result_service


def make_field(field: str = "w2_wages", value: float = 85000.00) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
    )


def test_save_extraction_result_persists_record(test_db):
    job_id = uuid4()
    document_id = uuid4()
    fields = [make_field()]

    result = result_service.save_extraction_result(
        test_db,
        job_id,
        document_id,
        None,
        "w2",
        fields,
    )

    assert result.job_id == str(job_id)
    assert result.document_id == str(document_id)


def test_save_extraction_result_sets_annual_income(test_db):
    fields = [make_field()]

    result = result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        None,
        "w2",
        fields,
    )

    assert result.annual_income == 85000.00


def test_get_case_summary_returns_total_and_sources(test_db):
    case_id = uuid4()
    first_field = make_field("w2_wages", 85000.00)
    second_field = make_field("agi", 79000.00)
    result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        case_id,
        "w2",
        [first_field],
    )
    result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        case_id,
        "tax_return",
        [second_field],
    )

    summary = result_service.get_case_summary(test_db, case_id)

    assert summary.total_annual_income == 82000.00
    assert [source.field for source in summary.sources] == ["w2_wages", "agi"]
