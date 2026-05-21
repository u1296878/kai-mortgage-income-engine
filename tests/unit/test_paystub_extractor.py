from uuid import uuid4

import pytest

from app.exceptions import ExtractionFailed
from app.extractors.paystub_extractor import extract_paystub_fields


def block(text, x1, y1, x2, y2):
    return {"text": text, "page": 1, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def paystub_blocks():
    return [
        block("Gross Pay", 50, 100, 120, 112),
        block("$3,269.23", 300, 100, 360, 112),
        block("YTD Gross", 50, 130, 120, 142),
        block("$42,500.00", 300, 130, 370, 142),
        block("Pay Date", 50, 160, 115, 172),
        block("2024-05-15", 300, 160, 370, 172),
        block("Pay Frequency", 50, 190, 140, 202),
        block("Biweekly", 300, 190, 360, 202),
        block("Salary", 50, 220, 90, 232),
    ]


def test_extract_gross_ytd_from_blocks():
    fields = extract_paystub_fields(paystub_blocks(), uuid4())

    assert next(field.value for field in fields if field.field == "gross_ytd") == 42500.0


def test_extract_gross_this_period_from_blocks():
    fields = extract_paystub_fields(paystub_blocks(), uuid4())

    assert next(field.value for field in fields if field.field == "gross_this_period") == 3269.23


def test_ytd_label_not_matched_as_gross_this_period():
    fields = extract_paystub_fields(paystub_blocks()[2:4], uuid4())

    assert "gross_this_period" not in {field.field for field in fields}


def test_extract_pay_period_type_biweekly():
    fields = extract_paystub_fields(paystub_blocks(), uuid4())
    period = next(field for field in fields if field.field == "pay_period_type")

    assert period.raw_text == "biweekly"


def test_extract_pay_date_from_blocks():
    fields = extract_paystub_fields(paystub_blocks(), uuid4())
    pay_date = next(field for field in fields if field.field == "pay_date")

    assert pay_date.raw_text == "2024-05-15"


def test_extract_income_type_salary():
    fields = extract_paystub_fields(paystub_blocks(), uuid4())
    income_type = next(field for field in fields if field.field == "income_type")

    assert income_type.raw_text == "salary"


def test_numeric_parsing_strips_currency_symbols():
    fields = extract_paystub_fields(paystub_blocks(), uuid4())

    assert next(field.value for field in fields if field.field == "gross_this_period") == 3269.23


def test_raises_when_no_gross_fields_found():
    blocks = [block("Net Pay", 50, 100, 100, 112), block("$100.00", 300, 100, 350, 112)]

    with pytest.raises(ExtractionFailed):
        extract_paystub_fields(blocks, uuid4())


def test_partial_results_returned_when_some_fields_missing():
    fields = extract_paystub_fields(paystub_blocks()[:4], uuid4())

    assert {field.field for field in fields} == {"gross_ytd", "gross_this_period"}


def test_value_bounding_box_used_not_label_bounding_box():
    fields = extract_paystub_fields(paystub_blocks(), uuid4())
    gross_ytd = next(field for field in fields if field.field == "gross_ytd")

    assert gross_ytd.bounding_box.x1 == 300.0
