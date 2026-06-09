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


def test_compute_annual_income_tax_return_is_reference_only():
    fields = [make_field("agi", 79000.00)]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "tax_return")

    assert annual_income is None
    assert confidence == "medium"
    assert notes == "Income derived from per-schedule drafts; AGI shown for reference only."


def test_compute_annual_income_tax_return_with_schedule_e_still_reference_only():
    fields = [
        make_field("agi", 73168.00),
        make_field("total_income", 75150.00),
        make_field("schedule_e_present", 1.0),
        make_field("schedule_e_net_rental_income", -1303.00),
    ]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "tax_return")

    assert annual_income is None
    assert confidence == "medium"
    assert "AGI shown for reference only" in notes


def test_compute_annual_income_tax_return_never_adds_gross_rents():
    fields = [
        make_field("agi", 73168.00),
        make_field("total_income", 75466.00),
        make_field("schedule_e_present", 1.0),
        make_field("schedule_e_gross_rents_total", 35980.00),
        make_field("schedule_e_net_rental_income", -1303.00),
    ]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "tax_return")

    assert annual_income is None
    assert "per-schedule drafts" in notes


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


def test_compute_annual_income_other_uses_rental_net_income_when_present():
    fields = [
        make_field("reported_income", 50000.00),
        make_field("rental_net_income", 18000.00),
    ]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "other")

    assert annual_income == 18000.00


def test_compute_annual_income_other_falls_back_to_reported_income():
    fields = [make_field("reported_income", 18000.00)]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "other")

    assert annual_income == 18000.00


def test_compute_annual_income_other_confidence_is_low():
    fields = [make_field("rental_net_income", 18000.00)]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "other")

    assert confidence == "low"


def test_summarize_case_income_sums_results():
    first_result = Result(annual_income=80000.00, extracted_fields=[])
    second_result = Result(annual_income=100000.00, extracted_fields=[])

    total, sources = income_service.summarize_case_income(
        [first_result, second_result],
    )

    assert total == 180000.00


def test_summarize_case_income_ignores_missing_annual_income():
    first_result = Result(annual_income=80000.00, extracted_fields=[])
    second_result = Result(annual_income=None, extracted_fields=[])

    total, sources = income_service.summarize_case_income(
        [first_result, second_result],
    )

    assert total == 80000.00


def test_summarize_case_income_flattens_sources():
    first_field = make_field("w2_wages", 85000.00)
    second_field = make_field("agi", 79000.00)
    first_result = Result(extracted_fields=[first_field.model_dump(mode="json")])
    second_result = Result(extracted_fields=[second_field.model_dump(mode="json")])

    total, sources = income_service.summarize_case_income(
        [first_result, second_result],
    )

    assert [source.field for source in sources] == ["w2_wages", "agi"]
