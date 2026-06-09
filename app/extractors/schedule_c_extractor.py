from uuid import UUID

from app.extractors.extracted_field_factory import make_numeric_field, parse_float
from app.extractors.tax_return_locator import (
    grouped_lines,
    line_anchors,
    nearby_value,
    nearest_money_value,
    value_candidate,
)
from app.extractors.tax_return_text import is_money, normalized_line_text
from app.schemas.extraction import ExtractedField

PART_V_ADDBACK_TOKENS = ("amortization", "amortiz", "casualty")

MONEY_LINES = {
    "net_profit": ("31", ("net", "profit")),
    "nonrecurring_income": ("6", ("other", "income")),
    "depletion": ("12", ("depletion",)),
    "depreciation": ("13", ("depreciation",)),
    "meals_entertainment_exclusion": ("24b", ("meals",)),
    "business_use_of_home": ("30", ("business", "use", "home")),
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
    if value := _part_v_amortization_casualty(blocks, page):
        fields.append(make_numeric_field(f"{prefix}_amortization_casualty", value, document_id))
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


def _part_v_amortization_casualty(blocks: list[dict], page: int) -> dict | None:
    values = []
    for line in _part_v_detail_lines(blocks, page):
        label_text = normalized_line_text([block for block in line if not is_money(block["text"])])
        if any(token in label_text for token in PART_V_ADDBACK_TOKENS):
            line_values = [block for block in line if is_money(block["text"])]
            if line_values:
                values.append(max(line_values, key=lambda block: block["x1"]))
    return _sum_value_blocks(values) if values else None


def _part_v_detail_lines(blocks: list[dict], page: int) -> list[list[dict]]:
    lines = sorted(grouped_lines(blocks).get(page, []), key=lambda line: line[0]["y1"])
    for index, line in enumerate(lines):
        text = normalized_line_text(line)
        if "part v" in text and "other expenses" in text:
            return lines[index + 1 :]
    return []


def _sum_value_blocks(values: list[dict]) -> dict:
    total = sum(parse_float(value["text"]) or 0.0 for value in values)
    return {
        "text": f"{total:.2f}",
        "page": values[0]["page"],
        "x1": min(value["x1"] for value in values),
        "y1": min(value["y1"] for value in values),
        "x2": max(value["x2"] for value in values),
        "y2": max(value["y2"] for value in values),
    }
