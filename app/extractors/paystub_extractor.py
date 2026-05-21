import re
from uuid import UUID

from app.extractors.block_utils import (
    distance,
    is_amount,
    is_right_or_below,
    line_for_block,
    merge_blocks,
)
from app.extractors.extracted_field_factory import make_numeric_field, make_text_field, parse_float
from app.extractors.paystub_patterns import DATE_LABELS, INCOME_TYPES, PERIOD_LABELS, PERIOD_TYPES, YTD_LABELS
from app.exceptions import ExtractionFailed
from app.schemas.extraction import ExtractedField


def extract_paystub_fields(blocks: list[dict], document_id: UUID) -> list[ExtractedField]:
    fields = []
    gross_ytd = _extract_numeric_field(blocks, YTD_LABELS)
    gross_period = _extract_period_gross(blocks)
    if gross_ytd:
        fields.append(make_numeric_field("gross_ytd", gross_ytd, document_id))
    if gross_period:
        fields.append(make_numeric_field("gross_this_period", gross_period, document_id))
    if not gross_ytd and not gross_period:
        raise ExtractionFailed("No pay stub gross income fields found")
    fields.extend(_extract_text_fields(blocks, document_id))
    return fields


def _extract_numeric_field(blocks: list[dict], labels: tuple[str, ...]) -> dict | None:
    matches = []
    for label in _label_anchors(blocks, labels):
        value = _nearest_numeric_value(label, blocks)
        if value:
            matches.append(value)
    if not matches:
        return None
    return max(matches, key=lambda block: parse_float(block["text"]) or 0.0)


def _extract_period_gross(blocks: list[dict]) -> dict | None:
    matches = [label for label in _label_anchors(blocks, PERIOD_LABELS) if "ytd" not in label["text"].lower()]
    values = [
        value
        for label in matches
        if (value := _nearest_numeric_value(label, blocks)) is not None
    ]
    if not values:
        return None
    return max(values, key=lambda block: parse_float(block["text"]) or 0.0)


def _matching_label(text: str, labels: tuple[str, ...]) -> str | None:
    clean_text = _normalize(text)
    return next((label for label in labels if label in clean_text), None)


def _label_anchors(blocks: list[dict], labels: tuple[str, ...]) -> list[dict]:
    anchors = []
    seen = set()
    for block in blocks:
        line = sorted(line_for_block(blocks, block), key=lambda item: item["x1"])
        for start_index in range(len(line)):
            words = []
            for word in line[start_index:]:
                if is_amount(word["text"]) or _is_date(word["text"]):
                    break
                words.append(word)
                if _matching_label(" ".join(item["text"] for item in words), labels):
                    key = (word["page"], word["x1"], word["y1"])
                    if key not in seen:
                        anchors.append(merge_blocks(words))
                        seen.add(key)
                    break
    return anchors


def _nearest_numeric_value(label: dict, blocks: list[dict]) -> dict | None:
    candidates = [
        block
        for block in blocks
        if is_amount(block["text"]) and _nearby_value(label, block)
    ]
    if not candidates:
        return None
    same_line = [block for block in candidates if abs(block["y1"] - label["y1"]) <= 5]
    if same_line:
        return max(same_line, key=lambda block: parse_float(block["text"]) or 0.0)
    return max(candidates, key=lambda block: parse_float(block["text"]) or 0.0)


def _nearby_value(label: dict, block: dict) -> bool:
    same_line = block["page"] == label["page"] and abs(block["y1"] - label["y1"]) <= 5
    near_vertical = block["page"] == label["page"] and abs(block["y1"] - label["y1"]) <= 50
    return (same_line or near_vertical) and is_right_or_below(label, block)


def _extract_text_fields(blocks: list[dict], document_id: UUID) -> list[ExtractedField]:
    fields = []
    period = _find_period_type(blocks)
    pay_date = _find_date_value(blocks)
    income_type = _find_income_type(blocks)
    if period:
        fields.append(make_text_field("pay_period_type", period, document_id))
    if pay_date:
        fields.append(make_text_field("pay_date", pay_date, document_id))
    if income_type:
        fields.append(make_text_field("income_type", income_type, document_id))
    return fields


def _find_period_type(blocks: list[dict]) -> dict | None:
    for block in blocks:
        clean_text = _normalize(block["text"])
        for keyword, normalized in PERIOD_TYPES.items():
            if keyword in clean_text:
                return {**block, "raw_text": normalized}
    return None


def _find_date_value(blocks: list[dict]) -> dict | None:
    for label in _label_anchors(blocks, DATE_LABELS):
        value = _nearest_text_value(label, blocks)
        if value:
            return value
    return None


def _nearest_text_value(label: dict, blocks: list[dict]) -> dict | None:
    candidates = [
        block
        for block in blocks
        if block["x1"] >= label["x2"]
        and _nearby_value(label, block)
        and not _matching_label(block["text"], DATE_LABELS)
    ]
    return min(candidates, key=lambda block: distance(label, block), default=None)


def _find_income_type(blocks: list[dict]) -> dict | None:
    for income_type in INCOME_TYPES:
        for block in blocks:
            if income_type in _normalize(block["text"]):
                return {**block, "raw_text": income_type}
    return None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace(":", " ")).strip()


def _is_date(text: str) -> bool:
    return re.fullmatch(r"\d{4}-\d{2}-\d{2}", text.strip()) is not None
