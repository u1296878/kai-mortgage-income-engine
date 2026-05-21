from uuid import uuid4

import pytest

from app.exceptions import ExtractionFailed
from app.extractors.w2_extractor import extract_w2_fields


def block(text, x1, y1, x2, y2):
    return {"text": text, "page": 1, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def clean_w2_blocks():
    return [
        block("Wages, tips, other compensation", 50, 100, 210, 115),
        block("85000.00", 250, 100, 320, 115),
        block("Federal income tax withheld", 50, 140, 210, 155),
        block("12000.00", 250, 140, 320, 155),
    ]


def test_extract_w2_wages_from_clean_blocks():
    fields = extract_w2_fields(clean_w2_blocks(), uuid4())

    assert {field.field for field in fields} >= {"w2_wages", "w2_federal_tax_withheld"}


def test_extract_w2_uses_value_bounding_box():
    fields = extract_w2_fields(clean_w2_blocks(), uuid4())
    wages = next(field for field in fields if field.field == "w2_wages")

    assert wages.bounding_box.x1 == 250.0
    assert wages.bounding_box.y1 == 100.0


def test_extract_w2_omits_missing_fields():
    fields = extract_w2_fields(clean_w2_blocks()[:2], uuid4())

    assert "w2_federal_tax_withheld" not in {field.field for field in fields}


def test_extract_w2_raises_when_no_fields_found():
    blocks = [block("not a tax form", 1, 2, 3, 4)]

    with pytest.raises(ExtractionFailed):
        extract_w2_fields(blocks, uuid4())


def test_extract_w2_returns_correct_document_id():
    document_id = uuid4()

    fields = extract_w2_fields(clean_w2_blocks(), document_id)

    assert all(field.document_id == document_id for field in fields)
