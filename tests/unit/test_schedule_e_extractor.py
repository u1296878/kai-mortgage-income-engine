import pytest

from app.exceptions import ExtractionFailed
from app.extractors.schedule_e_extractor import extract_schedule_e_properties
from tests.unit.tax_return_test_helpers import block


def test_extracts_per_property_schedule_e_line_items():
    properties = {prop.column: prop for prop in extract_schedule_e_properties(schedule_e_blocks())}

    assert properties["A"].address == "131 E 500 S Provo UT 84606"
    assert properties["A"].fair_rental_days == 366.0
    assert properties["A"].rents_received == 22480.0
    assert properties["A"].insurance == 211.0
    assert properties["A"].other_interest == 4280.0
    assert properties["B"].fair_rental_days == 240.0
    assert properties["B"].mortgage_interest == 5264.0
    assert properties["B"].depreciation_depletion == 4049.0


def test_rejects_schedule_e_when_column_sum_mismatches_total():
    blocks = schedule_e_blocks(total_rents="99,999.00")

    with pytest.raises(ExtractionFailed):
        extract_schedule_e_properties(blocks)


def test_handles_single_property_schedule_e():
    blocks = [item for item in schedule_e_blocks() if item["text"] not in {"B", "2221", "Corby", "Blvd", "South", "Bend", "IN", "46615", "13,500.00", "12,597.00", "4,049.00", "889.00"}]
    blocks = [block_ if block_["text"] != "35,980.00" else {**block_, "text": "22,480.00"} for block_ in blocks]
    blocks = [block_ if block_["text"] != "32,540.00" else {**block_, "text": "19,943.00"} for block_ in blocks]
    blocks = [block_ if block_["text"] != "12,165.00" else {**block_, "text": "8,116.00"} for block_ in blocks]

    properties = extract_schedule_e_properties(blocks)

    assert [prop.column for prop in properties] == ["A"]


def schedule_e_blocks(total_rents="35,980.00"):
    return [
        block("SCHEDULE", 50, 50, 120, 62, page=2),
        block("E", 124, 50, 132, 62, page=2),
        block("Supplemental", 136, 50, 220, 62, page=2),
        block("Income", 224, 50, 270, 62, page=2),
        block("and", 274, 50, 296, 62, page=2),
        block("Loss", 300, 50, 330, 62, page=2),
        block("1a", 50, 100, 66, 112, page=2),
        block("Physical", 72, 100, 126, 112, page=2),
        block("address", 130, 100, 180, 112, page=2),
        block("property", 236, 100, 292, 112, page=2),
        block("A", 50, 120, 58, 132, page=2),
        block("131", 72, 120, 92, 132, page=2),
        block("E", 96, 120, 104, 132, page=2),
        block("500", 108, 120, 132, 132, page=2),
        block("S", 136, 120, 144, 132, page=2),
        block("Provo", 148, 120, 184, 132, page=2),
        block("UT", 188, 120, 204, 132, page=2),
        block("84606", 208, 120, 244, 132, page=2),
        block("B", 50, 140, 58, 152, page=2),
        block("2221", 72, 140, 104, 152, page=2),
        block("Corby", 108, 140, 146, 152, page=2),
        block("Blvd", 150, 140, 180, 152, page=2),
        block("South", 184, 140, 222, 152, page=2),
        block("Bend", 226, 140, 258, 152, page=2),
        block("IN", 262, 140, 276, 152, page=2),
        block("46615", 280, 140, 316, 152, page=2),
        block("A", 50, 180, 58, 192, page=2),
        block("366", 420, 180, 444, 192, page=2),
        block("B", 50, 200, 58, 212, page=2),
        block("240", 420, 200, 444, 212, page=2),
        block("Income", 50, 230, 90, 242, page=2),
        block("A", 420, 230, 428, 242, page=2),
        block("B", 500, 230, 508, 242, page=2),
        block("C", 580, 230, 588, 242, page=2),
        *_amount_line("3", "Rents received", "22,480.00", "13,500.00", 260),
        *_amount_line("9", "Insurance", "211.00", None, 280),
        *_amount_line("12", "Mortgage interest", None, "5,264.00", 300),
        *_amount_line("13", "Other interest", "4,280.00", None, 320),
        *_amount_line("16", "Taxes", "1,677.00", "889.00", 340),
        *_amount_line("18", "Depreciation expense", "8,116.00", "4,049.00", 360),
        *_amount_line("20", "Total expenses", "19,943.00", "12,597.00", 380),
        *_total_line("23a", "Total line 3 rental properties", total_rents, 420),
        *_total_line("23c", "Total line 12 properties", "5,264.00", 440),
        *_total_line("23d", "Total line 18 properties", "12,165.00", 460),
        *_total_line("23e", "Total line 20 properties", "32,540.00", 480),
    ]


def _amount_line(number, label, amount_a, amount_b, y):
    row = [block(number, 50, y, 66, y + 12, page=2), block(label, 72, y, 210, y + 12, page=2)]
    if amount_a:
        row.append(block(amount_a, 420, y, 486, y + 12, page=2))
    if amount_b:
        row.append(block(amount_b, 500, y, 566, y + 12, page=2))
    return row


def _total_line(number, label, amount, y):
    return [
        block(number, 50, y, 74, y + 12, page=2),
        block(label, 78, y, 300, y + 12, page=2),
        block(amount, 500, y, 566, y + 12, page=2),
    ]
