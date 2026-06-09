from math import inf

from app.extractors.tax_return_text import is_money, normalize

IRS_FORM_REFERENCES = {"8829", "4562", "6198", "8995", "1040"}
ROW_TOLERANCE = 10


def line_amount_value(blocks: list[dict], page: int, line_number: str) -> dict | None:
    page_blocks = [block for block in blocks if block["page"] == page]
    amount_band = _amount_column_band(page_blocks)
    if amount_band is None:
        return None
    values = [
        value
        for anchor in _line_number_blocks(page_blocks, line_number)
        for value in _row_money_blocks(page_blocks, anchor["y1"], amount_band)
    ]
    return max(values, key=lambda block: block["x1"]) if values else None


def _amount_column_band(page_blocks: list[dict]) -> tuple[float, float] | None:
    for anchor in sorted(_line_number_blocks(page_blocks, "31"), key=lambda block: block["y1"]):
        values = _row_money_blocks(page_blocks, anchor["y1"], (anchor["x2"] + 20, inf))
        if values:
            amount = max(values, key=lambda block: block["x1"])
            pad = max(18.0, (amount["x2"] - amount["x1"]) * 0.5)
            return amount["x1"] - pad, amount["x2"] + pad
    return None


def _line_number_blocks(page_blocks: list[dict], line_number: str) -> list[dict]:
    left_limit = _left_line_number_limit(page_blocks)
    return [
        block
        for block in page_blocks
        if normalize(block["text"]) == line_number and block["x1"] <= left_limit
    ]


def _left_line_number_limit(page_blocks: list[dict]) -> float:
    return min((block["x1"] for block in page_blocks), default=0.0) + 180.0


def _row_money_blocks(
    page_blocks: list[dict],
    row_y: float,
    amount_band: tuple[float, float],
) -> list[dict]:
    low_x, high_x = amount_band
    return [
        block
        for block in page_blocks
        if is_money(block["text"])
        and abs(block["y1"] - row_y) <= ROW_TOLERANCE
        and low_x <= block["x1"] <= high_x
        and not _is_form_reference(block, page_blocks, row_y)
    ]


def _is_form_reference(block: dict, page_blocks: list[dict], row_y: float) -> bool:
    clean = normalize(block["text"])
    if clean not in IRS_FORM_REFERENCES:
        return False
    row_words = [
        normalize(candidate["text"])
        for candidate in page_blocks
        if abs(candidate["y1"] - row_y) <= ROW_TOLERANCE and candidate["x2"] <= block["x1"]
    ]
    return "form" in row_words[-3:] or "see" in row_words[-3:]
