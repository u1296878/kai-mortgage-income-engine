from tests.unit.schedule_c_extractor_fixtures import (
    fields_for,
    ocr_style,
    schedule_c_page,
    schedule_c_subtotal,
    value,
    values,
)
from tests.unit.tax_return_test_helpers import block, field_map, tax_return_blocks


def test_extract_schedule_c_business_fields_from_each_schedule_c_page():
    fields = field_map(
        tax_return_blocks()
        + _simple_schedule_c_page(page=2, net="50,000.00", depreciation="8,000.00", miles="1000")
        + _simple_schedule_c_page(page=3, net="25,000.00", depreciation="4,000.00", miles="0")
    )

    assert fields["schedule_c_business_1_net_profit"].value == 50000.0
    assert fields["schedule_c_business_1_depreciation"].value == 8000.0
    assert fields["schedule_c_business_1_business_miles"].value == 1000.0
    assert fields["schedule_c_business_2_net_profit"].value == 25000.0
    assert fields["schedule_c_business_2_depreciation"].value == 4000.0


def test_extract_schedule_c_addback_source_boxes_use_values():
    fields = field_map(tax_return_blocks() + _simple_schedule_c_page(page=2, net="50,000.00"))

    assert fields["schedule_c_business_1_business_use_of_home"].value == 3000.0
    assert fields["schedule_c_business_1_business_use_of_home"].bounding_box.x1 == 500.0


def test_wrapped_line_13_uses_depreciation_amount_not_line_23_taxes():
    fields = fields_for(schedule_c_page(depreciation="3,633.00", taxes="10,959.00"))

    assert value(fields, "depreciation") == 3633.0


def test_line_30_uses_business_home_amount_not_form_8829_reference():
    fields = fields_for(schedule_c_page(home="4,628.00"))

    assert value(fields, "business_use_of_home") == 4628.0


def test_line_6_does_not_use_nearby_gross_receipts():
    fields = fields_for(schedule_c_page())

    assert value(fields, "nonrecurring_income") == 0.0


def test_other_expenses_total_is_not_added_back_without_part_v_amortization():
    fields = fields_for(schedule_c_page(other_expenses="7,557.00", ordinary_part_v=True))

    assert value(fields, "amortization_casualty") == 0.0


def test_part_v_amortization_detail_is_added_back_without_27a_total():
    fields = fields_for(schedule_c_page(other_expenses="7,557.00", part_v_amortization=True))

    assert value(fields, "amortization_casualty") == 1200.0


def test_digital_and_ocr_style_blocks_extract_identical_fields():
    digital = schedule_c_page(net="85,247.00", depreciation="659.00", home="3,173.00", other_expenses="5,046.00")

    assert values(fields_for(digital)) == values(fields_for(ocr_style(digital)))


def test_2023_schedule_c_ties_out_without_27a_over_add():
    fields = fields_for(schedule_c_page())

    assert schedule_c_subtotal(fields, tax_year=2023) == 102641.0


def test_2024_schedule_c_ties_out_without_27a_over_add():
    fields = fields_for(schedule_c_page(net="85,247.00", depreciation="659.00", home="3,173.00", other_expenses="5,046.00"))

    assert schedule_c_subtotal(fields, tax_year=2024) == 89079.0


def _simple_schedule_c_page(page: int, net: str, depreciation: str = "8,000.00", miles: str = "0"):
    return [
        block("Schedule", 50, 50, 110, 62, page=page),
        block("C", 114, 50, 124, 62, page=page),
        block("Profit", 128, 50, 166, 62, page=page),
        block("or", 170, 50, 184, 62, page=page),
        block("Loss", 188, 50, 220, 62, page=page),
        block("From", 224, 50, 256, 62, page=page),
        block("Business", 260, 50, 320, 62, page=page),
        block("13", 50, 180, 66, 192, page=page),
        block("Depreciation", 72, 180, 150, 192, page=page),
        block(depreciation, 500, 180, 556, 192, page=page),
        block("30", 50, 300, 66, 312, page=page),
        block("Business", 72, 300, 130, 312, page=page),
        block("use", 134, 300, 158, 312, page=page),
        block("of", 162, 300, 176, 312, page=page),
        block("home", 180, 300, 214, 312, page=page),
        block("3,000.00", 500, 300, 556, 312, page=page),
        block("31", 50, 340, 66, 352, page=page),
        block("Net", 72, 340, 96, 352, page=page),
        block("profit", 100, 340, 136, 352, page=page),
        block(net, 500, 340, 570, 352, page=page),
        block("44a", 50, 420, 74, 432, page=page),
        block("Business", 72, 420, 130, 432, page=page),
        block("miles", 134, 420, 170, 432, page=page),
        block(miles, 500, 420, 540, 432, page=page),
    ]
