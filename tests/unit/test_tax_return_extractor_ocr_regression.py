from tests.unit.tax_return_test_helpers import block, field_map
from tests.unit.test_tax_return_extractor_regression import federal_1040_blocks


def test_blank_form_1040_line_1a_does_not_use_instruction_numbers():
    blocks = [
        item
        for item in federal_1040_blocks()
        if not (item["text"] == "94,380.00" and item["y1"] == 140)
    ]
    blocks += [
        block("Taxable", 263, 160, 315, 172),
        block("dependent", 320, 160, 390, 172),
        block("care", 394, 160, 430, 172),
        block("benefits", 434, 160, 490, 172),
        block("from", 494, 160, 530, 172),
        block("Form", 534, 160, 570, 172),
        block("2441,", 574, 160, 620, 172),
        block("line", 624, 160, 660, 172),
        block("26", 664, 160, 684, 172),
    ]

    fields = field_map(blocks)

    assert "wages" not in fields
    assert fields["total_income"].value == 94380.0


def test_schedule_c_line_31_uses_continuation_value_row():
    blocks = federal_1040_blocks()
    blocks += _schedule_c_header(page=4)
    blocks += [
        block("31", 50, 340, 66, 352, page=4),
        block("Net", 72, 340, 96, 352, page=4),
        block("profit", 100, 340, 136, 352, page=4),
        block("or", 140, 340, 154, 352, page=4),
        block("loss", 158, 340, 188, 352, page=4),
        block("Subtract", 192, 340, 250, 352, page=4),
        block("line", 254, 340, 284, 352, page=4),
        block("29.", 288, 340, 310, 352, page=4),
        block("Form", 192, 380, 228, 392, page=4),
        block("1041,", 232, 380, 274, 392, page=4),
        block("line", 278, 380, 308, 392, page=4),
        block("3.", 312, 380, 326, 392, page=4),
        block("31", 500, 380, 516, 392, page=4),
        block("85,247.", 560, 380, 620, 392, page=4),
    ]

    fields = field_map(blocks)

    assert fields["schedule_c_net"].value == 85247.0


def test_schedule_se_reference_to_schedule_c_line_31_is_not_schedule_c_page():
    blocks = federal_1040_blocks()
    blocks += [
        block("Schedule", 50, 300, 110, 312, page=5),
        block("SE", 114, 300, 132, 312, page=5),
        block("Self-Employment", 136, 300, 240, 312, page=5),
        block("Tax", 244, 300, 270, 312, page=5),
        block("2.", 50, 340, 64, 352, page=5),
        block("Net", 72, 340, 96, 352, page=5),
        block("profit", 100, 340, 136, 352, page=5),
        block("from", 140, 340, 176, 352, page=5),
        block("Schedule", 180, 340, 240, 352, page=5),
        block("C,", 244, 340, 260, 352, page=5),
        block("line", 264, 340, 294, 352, page=5),
        block("31", 298, 340, 314, 352, page=5),
        block("85,247.", 500, 340, 560, 352, page=5),
    ]

    fields = field_map(blocks)

    assert "schedule_c_net" not in fields


def _schedule_c_header(page: int):
    return [
        block("Schedule", 50, 300, 110, 312, page=page),
        block("C", 114, 300, 124, 312, page=page),
        block("Profit", 128, 300, 166, 312, page=page),
        block("or", 170, 300, 184, 312, page=page),
        block("Loss", 188, 300, 220, 312, page=page),
        block("From", 224, 300, 256, 312, page=page),
        block("Business", 260, 300, 320, 312, page=page),
    ]
