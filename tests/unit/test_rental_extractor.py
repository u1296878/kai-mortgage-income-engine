from uuid import uuid4

import pytest

from app.exceptions import ExtractionFailed
from app.extractors.rental_extractor import extract_rental_fields


def block(text, x1, y1, x2, y2):
    return {"text": text, "page": 1, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def rental_blocks(include_net=True):
    blocks = [
        block("Schedule", 50, 50, 110, 62),
        block("E", 114, 50, 124, 62),
        block("Supplemental", 128, 50, 216, 62),
        block("Income", 220, 50, 266, 62),
        block("and", 270, 50, 294, 62),
        block("Loss", 298, 50, 330, 62),
        block("2023", 450, 50, 482, 62),
        block("Property", 50, 90, 106, 102),
        block("Address:", 110, 90, 166, 102),
        block("123", 170, 90, 194, 102),
        block("Sample", 198, 90, 246, 102),
        block("Rental", 250, 90, 294, 102),
        block("Ave", 298, 90, 324, 102),
        block("3", 50, 140, 58, 152),
        block("Rents", 72, 140, 110, 152),
        block("received", 114, 140, 172, 152),
        block("24000.00", 500, 140, 556, 152),
        block("20", 50, 180, 66, 192),
        block("Total", 72, 180, 106, 192),
        block("expenses", 110, 180, 170, 192),
        block("6000.00", 500, 180, 550, 192),
    ]
    if include_net:
        blocks.extend([
            block("21", 50, 220, 66, 232),
            block("Income", 72, 220, 118, 232),
            block("or", 122, 220, 136, 232),
            block("loss", 140, 220, 170, 232),
            block("18000.00", 500, 220, 556, 232),
        ])
    return blocks


def field_map(blocks):
    return {field.field: field for field in extract_rental_fields(blocks, uuid4())}


def test_extract_rental_gross_income_from_blocks():
    fields = field_map(rental_blocks())

    assert fields["rental_gross_income"].value == 24000.0


def test_extract_rental_expenses_from_blocks():
    fields = field_map(rental_blocks())

    assert fields["rental_expenses"].value == 6000.0


def test_extract_rental_net_income_from_blocks():
    fields = field_map(rental_blocks())

    assert fields["rental_net_income"].value == 18000.0


def test_reported_income_matches_rental_net_income():
    fields = field_map(rental_blocks())

    assert fields["reported_income"].value == fields["rental_net_income"].value


def test_extract_tax_year_from_schedule_e_title():
    fields = field_map(rental_blocks())

    assert fields["tax_year"].value == 2023.0


def test_extract_property_address_as_raw_text():
    fields = field_map(rental_blocks())

    assert fields["property_address"].value == 0.0
    assert fields["property_address"].raw_text == "123 Sample Rental Ave"


def test_computes_net_income_when_gross_and_expenses_exist_without_net_line():
    fields = field_map(rental_blocks(include_net=False))

    assert fields["rental_net_income"].value == 18000.0
    assert fields["reported_income"].value == 18000.0


def test_numeric_parsing_handles_currency_commas():
    blocks = [item.copy() for item in rental_blocks()]
    next(item for item in blocks if item["text"] == "24000.00")["text"] = "$24,000.00"

    fields = field_map(blocks)

    assert fields["rental_gross_income"].value == 24000.0


def test_numeric_parsing_handles_parentheses_as_negative():
    blocks = [item.copy() for item in rental_blocks()]
    next(item for item in blocks if item["text"] == "6000.00")["text"] = "(6,000.00)"

    fields = field_map(blocks)

    assert fields["rental_expenses"].value == -6000.0


def test_negative_net_income_is_allowed():
    blocks = [item.copy() for item in rental_blocks()]
    next(item for item in blocks if item["text"] == "18000.00")["text"] = "(2,000.00)"

    fields = field_map(blocks)

    assert fields["rental_net_income"].value == -2000.0
    assert fields["reported_income"].value == -2000.0


def test_raises_when_no_rental_income_fields_found():
    blocks = [block("Not", 50, 50, 74, 62), block("rental", 78, 50, 120, 62)]

    with pytest.raises(ExtractionFailed):
        extract_rental_fields(blocks, uuid4())


def test_value_bounding_box_used_not_label_bounding_box():
    fields = field_map(rental_blocks())

    assert fields["rental_net_income"].bounding_box.x1 == 500.0


def test_required_fields_have_nonzero_bounding_boxes():
    fields = field_map(rental_blocks())

    for field_name in ("reported_income", "rental_net_income", "rental_gross_income", "rental_expenses", "tax_year"):
        assert fields[field_name].bounding_box.x1 > 0.0
