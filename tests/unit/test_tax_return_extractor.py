import pytest
from uuid import uuid4

from app.exceptions import ExtractionFailed
from app.extractors.tax_return_extractor import extract_tax_return_fields
from tests.unit.tax_return_test_helpers import (
    block,
    field_map,
    schedule_c_blocks,
    schedule_e_blocks,
    tax_return_blocks,
)


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


def test_extract_schedule_e_presence_when_attached():
    fields = field_map(tax_return_blocks() + schedule_e_blocks())

    assert fields["schedule_e_present"].value == 1.0
    assert fields["schedule_e_present"].raw_text == "Schedule E"


def test_extract_schedule_e_property_gross_rents_by_column():
    fields = field_map(tax_return_blocks() + schedule_e_blocks())

    assert fields["schedule_e_property_a_gross_rents"].value == 22480.0
    assert fields["schedule_e_property_b_gross_rents"].value == 13500.0
    assert fields["schedule_e_gross_rents_total"].value == 35980.0


def test_extract_schedule_e_property_addresses():
    fields = field_map(tax_return_blocks() + schedule_e_blocks())

    assert fields["schedule_e_property_a_address"].raw_text == "131 E 500 S Provo UT 84606"
    assert fields["schedule_e_property_b_address"].raw_text == "2221 Corby Blvd South Bend IN 46615"


def test_extract_schedule_e_line_26_net_rental_income():
    fields = field_map(tax_return_blocks() + schedule_e_blocks(net="(1,303.00)"))

    assert fields["schedule_e_net_rental_income"].value == -1303.0
    assert fields["schedule_e_net_rental_income"].bounding_box.x1 == 540.0
