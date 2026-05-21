import re
from uuid import UUID

from app.extractors.block_utils import (
    distance,
    is_amount,
    is_numeric,
    is_right_or_below,
    line_for_block,
    line_text,
    merge_blocks,
)
from app.exceptions import ExtractionFailed
from app.schemas.extraction import BoundingBox, ExtractedField

FIELD_PATTERNS = {
    "w2_wages": ("wages", "tips", "compensation"),
    "w2_federal_tax_withheld": ("federal", "income", "tax", "withheld"),
    "w2_social_security_wages": ("social", "security", "wages"),
    "w2_medicare_wages": ("medicare", "wages", "tips"),
}

BOX_PATTERNS = {
    "1": "w2_wages",
    "2": "w2_federal_tax_withheld",
    "3": "w2_social_security_wages",
    "5": "w2_medicare_wages",
}


def extract_w2_fields(blocks: list[dict], document_id: UUID) -> list[ExtractedField]:
    blocks = _form_blocks(blocks)
    fields = []
    for field_name, tokens in FIELD_PATTERNS.items():
        value = _find_value_for_label(blocks, tokens)
        if value:
            fields.append(_field_from_block(field_name, value, document_id))
    fields.extend(_extract_text_fields(blocks, document_id))
    if not fields:
        raise ExtractionFailed("No W-2 fields found")
    return _dedupe_fields(fields)


def _form_blocks(blocks: list[dict]) -> list[dict]:
    pages = {
        block["page"]
        for block in blocks
        if "wages" in line_text(blocks, block)
        and "federal income tax withheld" in line_text(blocks, block)
    }
    if not pages:
        return blocks
    return [block for block in blocks if block["page"] in pages]


def _find_value_for_label(blocks: list[dict], tokens: tuple[str, ...]) -> dict | None:
    for label in _find_label_anchors(blocks, tokens):
        value = _nearest_numeric_value(label, blocks)
        if value:
            return value
    box_value = _find_box_value(blocks, tokens)
    return box_value


def _find_label_anchors(blocks: list[dict], tokens: tuple[str, ...]) -> list[dict]:
    anchors = []
    for block in blocks:
        line = line_for_block(blocks, block)
        label_words = [word for word in line if not is_numeric(word["text"])]
        text = " ".join(word["text"].lower() for word in label_words)
        if all(token in text for token in tokens):
            anchors.append(merge_blocks(label_words))
    return anchors


def _nearest_numeric_value(label: dict, blocks: list[dict]) -> dict | None:
    candidates = [
        block
        for block in blocks
        if is_amount(block["text"]) and is_right_or_below(label, block)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda block: distance(label, block))


def _find_box_value(blocks: list[dict], tokens: tuple[str, ...]) -> dict | None:
    for box_number, field_name in BOX_PATTERNS.items():
        if FIELD_PATTERNS[field_name] != tokens:
            continue
        for block in blocks:
            if block["text"].strip().lower() in {box_number, f"box {box_number}"}:
                value = _nearest_numeric_value(block, blocks)
                if value:
                    return value
    return None


def _field_from_block(name: str, block: dict, document_id: UUID) -> ExtractedField:
    value = float(block["text"].replace("$", "").replace(",", ""))
    return _make_field(name, value, block, document_id)


def _extract_text_fields(blocks: list[dict], document_id: UUID) -> list[ExtractedField]:
    fields = []
    employer = _find_after_text(blocks, ("employer", "name"))
    if employer:
        fields.append(_make_field("w2_employer_name", 0.0, employer, document_id, employer["text"]))
    tax_year = next((block for block in blocks if re.fullmatch(r"20\d{2}", block["text"])), None)
    if tax_year:
        fields.append(_make_field("w2_tax_year", float(tax_year["text"]), tax_year, document_id))
    return fields


def _find_after_text(blocks: list[dict], tokens: tuple[str, ...]) -> dict | None:
    for label in _find_label_anchors(blocks, tokens):
        return min(
            (candidate for candidate in blocks if is_right_or_below(label, candidate)),
            key=lambda candidate: distance(label, candidate),
            default=None,
        )
    return None


def _make_field(
    name: str,
    value: float,
    block: dict,
    document_id: UUID,
    raw_text: str | None = None,
) -> ExtractedField:
    return ExtractedField(
        field=name,
        value=value,
        document_id=document_id,
        page=block["page"],
        bounding_box=BoundingBox(x1=block["x1"], y1=block["y1"], x2=block["x2"], y2=block["y2"]),
        raw_text=raw_text,
    )


def _dedupe_fields(fields: list[ExtractedField]) -> list[ExtractedField]:
    found = set()
    unique = []
    for field in fields:
        if field.field in found:
            continue
        found.add(field.field)
        unique.append(field)
    return unique
