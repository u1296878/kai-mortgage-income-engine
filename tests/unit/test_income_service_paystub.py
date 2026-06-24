from uuid import uuid4

from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import income_service


def make_field(field: str, value: float, raw_text: str | None = None) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
        raw_text=raw_text,
    )


def test_paystub_result_income_is_reference_only():
    fields = [make_field("gross_ytd", 42500.0)]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "pay_stub")

    assert annual_income is None
    assert confidence == "medium"
    assert "employment draft" in notes
