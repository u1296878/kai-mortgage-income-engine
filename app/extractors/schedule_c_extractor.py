from uuid import UUID

from app.extractors.extracted_field_factory import make_numeric_field, parse_float
from app.extractors.tax_return_locator import (
    line_anchors,
    nearby_value,
    nearest_money_value,
    value_candidate,
)
from app.schemas.extraction import ExtractedField

MONEY_LINES = {
    "net_profit": ("31", ("net", "profit")),
    "nonrecurring_income": ("6", ("other", "income")),
    "depletion": ("12", ("depletion",)),
    "depreciation": ("13", ("depreciation",)),
    "meals_entertainment_exclusion": ("24b", ("meals",)),
    "business_use_of_home": ("30", ("business", "use", "home")),
    "amortization_casualty": ("27a", ("other", "expenses")),
}

NUMERIC_LINES = {
    "business_miles": ("44a", ("business", "miles")),
}


def extract_schedule_c_fields(
    blocks: list[dict],
    document_id: UUID,
    pages: set[int],
) -> list[ExtractedField]:
    fields: list[ExtractedField] = []
    for index, page in enumerate(sorted(pages), start=1):
        fields.extend(_business_fields(blocks, document_id, page, index))
    return fields


def _business_fields(
    blocks: list[dict],
    document_id: UUID,
    page: int,
    index: int,
) -> list[ExtractedField]:
    prefix = f"schedule_c_business_{index}"
    fields = []
    for name, (line_number, tokens) in MONEY_LINES.items():
        value = _line_money_value(blocks, page, line_number, tokens)
        if value:
            fields.append(make_numeric_field(f"{prefix}_{name}", value, document_id))
    for name, (line_number, tokens) in NUMERIC_LINES.items():
        value = _line_numeric_value(blocks, page, line_number, tokens)
        if value:
            fields.append(make_numeric_field(f"{prefix}_{name}", value, document_id))
    return fields


def _line_money_value(
    blocks: list[dict],
    page: int,
    line_number: str,
    tokens: tuple[str, ...],
) -> dict | None:
    values = [
        value
        for label in line_anchors(blocks, line_number, tokens, {page})
        if (value := nearest_money_value(label, blocks, line_number)) is not None
    ]
    return values[0] if values else None


def _line_numeric_value(
    blocks: list[dict],
    page: int,
    line_number: str,
    tokens: tuple[str, ...],
) -> dict | None:
    values = [
        value
        for label in line_anchors(blocks, line_number, tokens, {page})
        if (value := _nearest_numeric_value(label, blocks)) is not None
    ]
    return values[0] if values else None


def _nearest_numeric_value(label: dict, blocks: list[dict]) -> dict | None:
    candidates = [
        block
        for block in blocks
        if parse_float(block["text"]) is not None
        and nearby_value(label, block)
        and value_candidate(label, block)
    ]
    if not candidates:
        return None
    same_line = [block for block in candidates if abs(block["y1"] - label["y1"]) <= 5]
    return max(same_line or candidates, key=lambda block: block["x1"])
