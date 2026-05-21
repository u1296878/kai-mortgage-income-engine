from uuid import uuid4

from app.models.result import Result
from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import income_service


def make_field(field: str, value: float) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
    )


def test_compute_annual_income_w2_returns_wages():
    fields = [make_field("w2_wages", 85000.00)]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "w2")

    assert annual_income == 85000.00


def test_compute_annual_income_bank_statement_annualizes():
    fields = [make_field("average_monthly_deposit", 7200.00)]

    annual_income, confidence, notes = income_service.compute_annual_income(
        fields,
        "bank_statement",
    )

    assert annual_income == 86400.00


def test_compute_annual_income_w2_confidence_is_high():
    fields = [make_field("w2_wages", 85000.00)]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "w2")

    assert confidence == "high"


def test_compute_annual_income_bank_statement_confidence_is_low():
    fields = [make_field("average_monthly_deposit", 7200.00)]

    annual_income, confidence, notes = income_service.compute_annual_income(
        fields,
        "bank_statement",
    )

    assert confidence == "low"


def test_summarize_case_income_averages_results():
    first_result = Result(annual_income=80000.00, extracted_fields=[])
    second_result = Result(annual_income=100000.00, extracted_fields=[])

    total, sources = income_service.summarize_case_income(
        [first_result, second_result],
    )

    assert total == 90000.00


def test_summarize_case_income_flattens_sources():
    first_field = make_field("w2_wages", 85000.00)
    second_field = make_field("agi", 79000.00)
    first_result = Result(extracted_fields=[first_field.model_dump(mode="json")])
    second_result = Result(extracted_fields=[second_field.model_dump(mode="json")])

    total, sources = income_service.summarize_case_income(
        [first_result, second_result],
    )

    assert [source.field for source in sources] == ["w2_wages", "agi"]
