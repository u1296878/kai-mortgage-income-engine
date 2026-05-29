import re
from uuid import UUID

from app.exceptions import ExtractionFailed
from app.extractors.block_utils import distance, line_for_block, merge_blocks
from app.extractors.extracted_field_factory import make_field, make_numeric_field, make_text_field, parse_float
from app.extractors.rental_patterns import ADDRESS_LABELS, FIELD_PATTERNS
from app.schemas.extraction import ExtractedField


def extract_rental_fields(blocks: list[dict], document_id: UUID) -> list[ExtractedField]:
    value_blocks = {
        name: _extract_value_block(blocks, patterns)
        for name, patterns in FIELD_PATTERNS.items()
    }
    if not value_blocks["rental_net_income"]:
        value_blocks["rental_net_income"] = _computed_net_block(value_blocks)
    fields = _income_fields(value_blocks, document_id)
    tax_year = _find_tax_year(blocks)
    address = _find_property_address(blocks)
    if tax_year:
        fields.append(make_numeric_field("tax_year", tax_year, document_id))
    if address:
        fields.append(make_text_field("property_address", address, document_id))
    if not any(field.field in {"rental_net_income", "rental_gross_income"} for field in fields):
        raise ExtractionFailed("No rental income fields found")
    if not any(field.field == "reported_income" for field in fields):
        raise ExtractionFailed("Rental document did not produce reported income")
    return fields


def _income_fields(value_blocks: dict[str, dict | None], document_id: UUID) -> list[ExtractedField]:
    fields = []
    for field_name in ("rental_gross_income", "rental_expenses", "rental_net_income"):
        if value_blocks[field_name]:
            fields.append(make_numeric_field(field_name, value_blocks[field_name], document_id))
    net_block = value_blocks["rental_net_income"]
    if net_block:
        fields.append(make_numeric_field("reported_income", net_block, document_id))
    return fields


def _computed_net_block(value_blocks: dict[str, dict | None]) -> dict | None:
    gross_block = value_blocks["rental_gross_income"]
    expense_block = value_blocks["rental_expenses"]
    if not gross_block or not expense_block:
        return None
    gross = parse_float(gross_block["text"])
    expenses = parse_float(expense_block["text"])
    if gross is None or expenses is None:
        return None
    return {**gross_block, "text": str(gross - expenses)}


def _extract_value_block(blocks: list[dict], patterns: tuple[tuple[str, tuple[str, ...]], ...]) -> dict | None:
    values = [
        value
        for label in _label_anchors(blocks, patterns)
        if (value := _nearest_money_value(label, blocks)) is not None
    ]
    return values[0] if values else None


def _label_anchors(blocks: list[dict], patterns: tuple[tuple[str, tuple[str, ...]], ...]) -> list[dict]:
    anchors = []
    seen = set()
    for line in _unique_lines(blocks):
        label_words = [block for block in line if not _is_money(block["text"])]
        text = _line_text(label_words)
        if _matches_any_pattern(text, patterns):
            key = (label_words[0]["page"], round(label_words[0]["y1"], 1), text)
            if key not in seen:
                anchors.append(merge_blocks(label_words))
                seen.add(key)
    return anchors


def _matches_any_pattern(text: str, patterns: tuple[tuple[str, tuple[str, ...]], ...]) -> bool:
    words = text.split()
    for line_number, tokens in patterns:
        line_matches = not line_number or line_number in words
        if line_matches and all(token in words for token in tokens):
            return True
    return False


def _nearest_money_value(label: dict, blocks: list[dict]) -> dict | None:
    candidates = [
        block
        for block in blocks
        if _is_money(block["text"]) and _nearby_value(label, block)
    ]
    if not candidates:
        return None
    same_line = [block for block in candidates if abs(block["y1"] - label["y1"]) <= 5]
    if same_line:
        return max(same_line, key=lambda block: block["x1"])
    return min(candidates, key=lambda block: distance(label, block))


def _nearby_value(label: dict, block: dict) -> bool:
    if block["page"] != label["page"]:
        return False
    same_line = abs(block["y1"] - label["y1"]) <= 5 and block["x1"] >= label["x2"]
    below = 0 <= block["y1"] - label["y1"] <= 80 and abs(block["x1"] - label["x1"]) < 260
    return same_line or below


def _find_tax_year(blocks: list[dict]) -> dict | None:
    for line in _unique_lines(blocks):
        text = _line_text(line)
        if "schedule e" in text or "supplemental income and loss" in text or "form 1040" in text:
            year = next((block for block in line if re.fullmatch(r"20\d{2}", block["text"])), None)
            if year:
                return year
    return next((block for block in blocks if re.fullmatch(r"20\d{2}", block["text"])), None)


def _find_property_address(blocks: list[dict]) -> dict | None:
    for line in _unique_lines(blocks):
        text = _line_text(line)
        if any(label in text for label in ADDRESS_LABELS):
            words = _address_words(line)
            if words:
                return {**merge_blocks(words), "raw_text": " ".join(block["text"].strip(":") for block in words)}
    return None


def _address_words(line: list[dict]) -> list[dict]:
    colon_index = next((index for index, block in enumerate(line) if ":" in block["text"]), None)
    if colon_index is not None:
        return line[colon_index + 1 :]
    return line[2:] if len(line) > 2 else []


def _unique_lines(blocks: list[dict]) -> list[list[dict]]:
    lines = []
    seen = set()
    for block in blocks:
        key = (block["page"], round(block["y1"]))
        if key not in seen:
            seen.add(key)
            lines.append(sorted(line_for_block(blocks, block), key=lambda item: item["x1"]))
    return lines


def _line_text(line: list[dict]) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", " ".join(block["text"].lower() for block in line))).strip()


def _is_money(text: str) -> bool:
    value = parse_float(text)
    if value is None:
        return False
    return any(marker in text.strip() for marker in ("$", ",", ".", "(", ")", "-")) or abs(value) >= 100
