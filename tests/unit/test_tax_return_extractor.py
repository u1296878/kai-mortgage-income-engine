from uuid import uuid4

import pytest

from app.exceptions import ExtractionFailed
from app.extractors.tax_return_extractor import extract_tax_return_fields


def block(text, x1, y1, x2, y2, page=1):
    return {"text": text, "page": page, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def tax_return_blocks():
    return [
        block("Form", 50, 50, 80, 62),
        block("1040", 84, 50, 116, 62),
        block("U.S.", 120, 50, 145, 62),
        block("Individual", 150, 50, 210, 62),
        block("Income", 214, 50, 260, 62),
        block("Tax", 264, 50, 288, 62),
        block("Return", 292, 50, 338, 62),
        block("2023", 450, 50, 482, 62),
        block("Filing", 50, 80, 90, 92),
        block("Status:", 94, 80, 140, 92),
        block("Single", 144, 80, 186, 92),
        block("1a", 50, 140, 66, 152),
        block("Total", 72, 140, 106, 152),
        block("amount", 110, 140, 160, 152),
        block("from", 164, 140, 194, 152),
        block("Form(s)", 198, 140, 246, 152),
        block("W-2,", 250, 140, 282, 152),
        block("box", 286, 140, 310, 152),
        block("1", 314, 140, 320, 152),
        block("85000.00", 500, 140, 556, 152),
        block("9", 50, 180, 58, 192),
        block("Total", 72, 180, 106, 192),
        block("income", 110, 180, 156, 192),
        block("90000.00", 500, 180, 556, 192),
        block("11", 50, 220, 66, 232),
        block("Adjusted", 72, 220, 130, 232),
        block("gross", 134, 220, 174, 232),
        block("income", 178, 220, 224, 232),
        block("79000.00", 500, 220, 556, 232),
    ]


def schedule_c_blocks(value="5000.00"):
    return [
        block("Schedule", 50, 300, 110, 312),
        block("C", 114, 300, 124, 312),
        block("Profit", 128, 300, 166, 312),
        block("or", 170, 300, 184, 312),
        block("Loss", 188, 300, 220, 312),
        block("From", 224, 300, 256, 312),
        block("Business", 260, 300, 320, 312),
        block("31", 50, 340, 66, 352),
        block("Net", 72, 340, 96, 352),
        block("profit", 100, 340, 136, 352),
        block("or", 140, 340, 154, 352),
        block("loss", 158, 340, 188, 352),
        block(value, 500, 340, 556, 352),
    ]


def field_map(blocks):
    return {field.field: field for field in extract_tax_return_fields(blocks, uuid4())}


def test_extract_agi_from_blocks():
    fields = field_map(tax_return_blocks())

    assert fields["agi"].value == 79000.0


def test_extract_wages_from_blocks():
    fields = field_map(tax_return_blocks())

    assert fields["wages"].value == 85000.0


def test_extract_total_income_from_blocks():
    fields = field_map(tax_return_blocks())

    assert fields["total_income"].value == 90000.0


def test_extract_tax_year_from_form_title():
    fields = field_map(tax_return_blocks())

    assert fields["tax_year"].value == 2023.0


def test_extract_filing_status_single_as_raw_text():
    fields = field_map(tax_return_blocks())

    assert fields["filing_status"].value == 0.0
    assert fields["filing_status"].raw_text == "single"


def test_extract_schedule_c_net_when_present():
    fields = field_map(tax_return_blocks() + schedule_c_blocks())

    assert fields["schedule_c_net"].value == 5000.0


def test_schedule_c_net_omitted_when_absent():
    fields = field_map(tax_return_blocks())

    assert "schedule_c_net" not in fields


def test_raises_when_no_income_fields_found():
    blocks = [block("not", 50, 50, 70, 62), block("a", 74, 50, 80, 62), block("return", 84, 50, 120, 62)]

    with pytest.raises(ExtractionFailed):
        extract_tax_return_fields(blocks, uuid4())


def test_value_bounding_box_used_not_label_bounding_box():
    fields = field_map(tax_return_blocks())

    assert fields["agi"].bounding_box.x1 == 500.0


def test_numeric_parsing_handles_currency_commas():
    blocks = [item.copy() for item in tax_return_blocks()]
    next(block for block in blocks if block["text"] == "79000.00")["text"] = "$79,000.00"

    fields = field_map(blocks)

    assert fields["agi"].value == 79000.0


def test_numeric_parsing_handles_parentheses_as_negative():
    fields = field_map(tax_return_blocks() + schedule_c_blocks("(5,000.00)"))

    assert fields["schedule_c_net"].value == -5000.0
