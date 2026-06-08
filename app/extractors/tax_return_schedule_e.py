from uuid import UUID

from app.extractors.block_utils import line_for_block, merge_blocks
from app.extractors.extracted_field_factory import (
    make_field,
    make_numeric_field,
    make_text_field,
    parse_float,
)
from app.extractors.tax_return_locator import (
    grouped_lines,
    is_money,
    line_anchors,
    nearest_money_value,
    normalize,
    normalized_line_text,
    unique_lines,
)
from app.schemas.extraction import ExtractedField

PROPERTY_RENT_FIELDS = (
    "schedule_e_property_a_gross_rents",
    "schedule_e_property_b_gross_rents",
    "schedule_e_property_c_gross_rents",
)
PROPERTY_ADDRESS_FIELDS = {
    "a": "schedule_e_property_a_address",
    "b": "schedule_e_property_b_address",
    "c": "schedule_e_property_c_address",
}


def extract_schedule_e_fields(
    blocks: list[dict],
    document_id: UUID,
) -> list[ExtractedField]:
    pages = schedule_e_pages(blocks)
    if not pages:
        return []
    fields = [make_field("schedule_e_present", 1.0, _header_block(blocks, pages), document_id, "Schedule E")]
    fields.extend(_property_address_fields(blocks, pages, document_id))
    rent_blocks = _line_money_values(blocks, "3", ("rents", "received"), pages)
    for field_name, value_block in zip(PROPERTY_RENT_FIELDS, rent_blocks):
        fields.append(make_numeric_field(field_name, value_block, document_id))
    total_gross = _line_value(blocks, "23a", ("total", "line", "3", "rental", "properties"), pages)
    if total_gross is None:
        total_gross = _sum_block(rent_blocks)
    if total_gross:
        fields.append(make_numeric_field("schedule_e_gross_rents_total", total_gross, document_id))
    net = _line_value(
        blocks,
        "26",
        ("total", "rental", "real", "estate", "income", "or", "loss"),
        pages,
    )
    if net:
        fields.append(make_numeric_field("schedule_e_net_rental_income", net, document_id))
    return fields


def schedule_e_pages(blocks: list[dict]) -> set[int]:
    return {page for page, lines in grouped_lines(blocks).items() if _page_score(lines) > 0}


def _page_score(lines: list[list[dict]]) -> int:
    header_text = " ".join(normalized_line_text(line) for line in lines[:15])
    if "schedule e" not in header_text or "supplemental income and loss" not in header_text:
        return 0
    return 5 if _page_has_line(lines, "3", ("rents", "received")) else 3


def _page_has_line(lines: list[list[dict]], line_number: str, tokens: tuple[str, ...]) -> bool:
    for line in lines:
        label_words = [block for block in line if not is_money(block["text"])]
        text = normalized_line_text(label_words)
        words = text.split()
        if line_number in words and all(token in words for token in tokens):
            return True
    return False


def _header_block(blocks: list[dict], pages: set[int]) -> dict:
    for line in unique_lines(blocks):
        if line[0]["page"] in pages and "schedule e" in normalized_line_text(line):
            return merge_blocks(line)
    first = next(block for block in blocks if block["page"] in pages)
    return first


def _property_address_fields(
    blocks: list[dict],
    pages: set[int],
    document_id: UUID,
) -> list[ExtractedField]:
    header = next(iter(line_anchors(blocks, "1a", ("physical", "address", "property"), pages)), None)
    if header is None:
        return []
    fields = []
    seen = set()
    for line in unique_lines(blocks):
        if line[0]["page"] != header["page"] or not 0 < line[0]["y1"] - header["y1"] <= 60:
            continue
        key = normalize(line[0]["text"])
        if key in PROPERTY_ADDRESS_FIELDS and len(line) > 1:
            address = merge_blocks(line[1:])
            raw_text = " ".join(block["text"] for block in line[1:])
            field_key = (PROPERTY_ADDRESS_FIELDS[key], raw_text)
            if field_key in seen:
                continue
            seen.add(field_key)
            fields.append(make_text_field(PROPERTY_ADDRESS_FIELDS[key], {**address, "raw_text": raw_text}, document_id))
    return fields


def _line_value(blocks: list[dict], line_number: str, tokens: tuple[str, ...], pages: set[int]) -> dict | None:
    values = [
        value
        for label in line_anchors(blocks, line_number, tokens, pages)
        if (value := nearest_money_value(label, blocks, line_number)) is not None
    ]
    return values[0] if values else None


def _line_money_values(blocks: list[dict], line_number: str, tokens: tuple[str, ...], pages: set[int]) -> list[dict]:
    for label in line_anchors(blocks, line_number, tokens, pages):
        values = [
            block
            for block in line_for_block(blocks, label)
            if is_money(block["text"]) and block["x1"] >= label["x1"]
        ]
        if values:
            return _dedupe_blocks(sorted(values, key=lambda block: block["x1"]))
    return []


def _dedupe_blocks(blocks: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for block in blocks:
        key = (block["text"], round(block["x1"], 1), round(block["y1"], 1))
        if key not in seen:
            deduped.append(block)
            seen.add(key)
    return deduped


def _sum_block(blocks: list[dict]) -> dict | None:
    values = [parse_float(block["text"]) for block in blocks]
    if not values or any(value is None for value in values):
        return None
    return {**merge_blocks(blocks), "text": str(sum(value for value in values if value is not None))}
