from uuid import uuid4

import pytest

from app.exceptions import ExtractionFailed
from app.extractors.bank_statement_extractor import extract_bank_statement_fields


def block(text, x1, y1, x2, y2):
    return {"text": text, "page": 1, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def bank_blocks(include_summary=True, include_period=True):
    blocks = [
        block("Sample", 50, 50, 92, 62),
        block("Bank", 96, 50, 126, 62),
        block("2024-01-15", 50, 140, 120, 152),
        block("Payroll", 130, 140, 176, 152),
        block("Deposit", 180, 140, 226, 152),
        block("ACME", 230, 140, 268, 152),
        block("Corp", 272, 140, 304, 152),
        block("5000.00", 500, 140, 550, 152),
        block("2024-02-15", 50, 170, 120, 182),
        block("Direct", 130, 170, 170, 182),
        block("Deposit", 174, 170, 220, 182),
        block("ACME", 224, 170, 262, 182),
        block("Corp", 266, 170, 298, 182),
        block("5000.00", 500, 170, 550, 182),
        block("2024-03-15", 50, 200, 120, 212),
        block("ACH", 130, 200, 158, 212),
        block("Credit", 162, 200, 202, 212),
        block("Payroll", 206, 200, 252, 212),
        block("5000.00", 500, 200, 550, 212),
        block("2024-01-20", 50, 240, 120, 252),
        block("Debit", 130, 240, 166, 252),
        block("Card", 170, 240, 200, 252),
        block("Purchase", 204, 240, 260, 252),
        block("-125.00", 500, 240, 550, 252),
        block("Beginning", 50, 280, 116, 292),
        block("Balance", 120, 280, 170, 292),
        block("1200.00", 500, 280, 550, 292),
        block("Ending", 50, 310, 94, 322),
        block("Balance", 98, 310, 148, 322),
        block("16200.00", 500, 310, 556, 322),
    ]
    if include_period:
        blocks.extend([
            block("Statement", 50, 90, 120, 102),
            block("Period:", 124, 90, 174, 102),
            block("2024-01-01", 180, 90, 250, 102),
            block("to", 254, 90, 268, 102),
            block("2024-03-31", 272, 90, 342, 102),
        ])
    if include_summary:
        blocks.extend([
            block("Total", 50, 350, 84, 362),
            block("Deposits", 88, 350, 146, 362),
            block("and", 150, 350, 174, 362),
            block("Credits", 178, 350, 224, 362),
            block("15000.00", 500, 350, 556, 362),
        ])
    return blocks


def field_map(blocks):
    return {field.field: field for field in extract_bank_statement_fields(blocks, uuid4())}


def test_extract_total_deposits_from_transaction_rows():
    fields = field_map(bank_blocks(include_summary=False))

    assert fields["total_deposits"].value == 15000.0


def test_extract_average_monthly_deposit():
    fields = field_map(bank_blocks())

    assert fields["average_monthly_deposit"].value == 5000.0


def test_extract_months_sampled_from_statement_period():
    fields = field_map(bank_blocks())

    assert fields["months_sampled"].value == 3.0


def test_extract_statement_dates_as_raw_text():
    fields = field_map(bank_blocks())

    assert fields["statement_start_date"].value == 0.0
    assert fields["statement_start_date"].raw_text == "2024-01-01"
    assert fields["statement_end_date"].raw_text == "2024-03-31"


def test_excludes_withdrawals_and_balances():
    fields = field_map(bank_blocks())

    assert fields["total_deposits"].value == 15000.0


def test_uses_total_deposits_summary_line_when_present():
    fields = field_map(bank_blocks())

    assert fields["total_deposits"].bounding_box.x1 == 500.0
    assert fields["total_deposits"].bounding_box.y1 == 350.0


def test_falls_back_to_transaction_sum_when_no_summary_line():
    fields = field_map(bank_blocks(include_summary=False))

    assert fields["total_deposits"].value == 15000.0


def test_falls_back_to_unique_transaction_months_when_statement_period_missing():
    fields = field_map(bank_blocks(include_summary=False, include_period=False))

    assert fields["months_sampled"].value == 3.0


def test_defaults_to_one_month_when_dates_missing():
    blocks = [
        block("Payroll", 50, 100, 96, 112),
        block("Deposit", 100, 100, 146, 112),
        block("5000.00", 500, 100, 550, 112),
    ]

    fields = field_map(blocks)

    assert fields["months_sampled"].value == 1.0


def test_raises_when_no_deposits_found():
    blocks = [block("Ending", 50, 100, 94, 112), block("Balance", 98, 100, 148, 112)]

    with pytest.raises(ExtractionFailed):
        extract_bank_statement_fields(blocks, uuid4())


def test_value_bounding_box_used_for_total_deposits():
    fields = field_map(bank_blocks())

    assert fields["total_deposits"].bounding_box.x1 == 500.0


def test_required_numeric_fields_have_nonzero_bounding_boxes():
    fields = field_map(bank_blocks())

    for field_name in ("average_monthly_deposit", "months_sampled", "total_deposits"):
        assert fields[field_name].bounding_box.x1 > 0.0
