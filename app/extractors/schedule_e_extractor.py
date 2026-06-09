from uuid import UUID

from app.exceptions import ExtractionFailed
from app.extractors.block_utils import merge_blocks
from app.extractors.extracted_field_factory import make_field, make_numeric_field, make_text_field, parse_float
from app.extractors.tax_return_block_index import TaxReturnBlockIndex, as_tax_return_index
from app.extractors.schedule_e_lines import (
    amount_blocks,
    continuation_value,
    find_line,
    line_matches,
    line_value,
    line_y,
    nearest_column,
)
from app.extractors.schedule_e_models import ScheduleEProperty
from app.extractors.tax_return_locator import grouped_lines, normalize, normalized_line_text, unique_lines
from app.schemas.extraction import ExtractedField

AMOUNT_LINES = {
    "rents_received": ("3", ("rents", "received")),
    "insurance": ("9", ("insurance",)),
    "mortgage_interest": ("12", ("mortgage", "interest")),
    "other_interest": ("13", ("other", "interest")),
    "taxes": ("16", ("taxes",)),
    "depreciation_depletion": ("18", ("depreciation",)),
    "total_expenses": ("20", ("total", "expenses")),
}
FIELD_SUFFIXES = {"rents_received": "gross_rents"}
TOTAL_LINES = {
    "rents_received": ("23a", ("line", "3", "rental", "properties")),
    "mortgage_interest": ("23c", ("line", "12", "properties")),
    "depreciation_depletion": ("23d", ("line", "18", "properties")),
    "total_expenses": ("23e", ("line", "20", "properties")),
}
def extract_schedule_e_properties(blocks: list[dict] | TaxReturnBlockIndex) -> list[ScheduleEProperty]:
    block_index = as_tax_return_index(blocks)
    properties: list[ScheduleEProperty] = []
    for page in sorted(schedule_e_pages(block_index)):
        page_blocks = block_index.page_blocks(page)
        columns = _column_positions(page_blocks)
        if not columns:
            continue
        page_properties = {column: ScheduleEProperty(column=column) for column in columns}
        _set_addresses(page_blocks, page_properties)
        _set_fair_rental_days(page_blocks, page_properties)
        _set_amount_lines(page_blocks, page_properties, columns)
        _validate_totals(page_blocks, page_properties)
        properties.extend(prop for prop in page_properties.values() if _has_property_income(prop))
    return properties

def extract_schedule_e_fields(blocks: list[dict] | TaxReturnBlockIndex, document_id: UUID) -> list[ExtractedField]:
    properties = extract_schedule_e_properties(blocks)
    if not properties:
        return []
    fields = [make_field("schedule_e_present", 1.0, _first_header(blocks), document_id, "Schedule E")]
    for prop in properties:
        fields.extend(_property_fields(prop, document_id))
    total = _total_block(properties, "rents_received", "schedule_e_gross_rents_total")
    if total:
        fields.append(make_numeric_field("schedule_e_gross_rents_total", total, document_id))
    net = continuation_value(
        blocks,
        "26",
        ("total", "rental", "real", "estate", "income", "or", "loss"),
        schedule_e_pages(blocks),
    )
    if net:
        fields.append(make_numeric_field("schedule_e_net_rental_income", net, document_id))
    return fields

def schedule_e_pages(blocks: list[dict] | TaxReturnBlockIndex) -> set[int]:
    return {page for page, lines in grouped_lines(blocks).items() if _page_score(lines) > 0}

def _page_score(lines: list[list[dict]]) -> int:
    header_text = " ".join(normalized_line_text(line) for line in lines[:15])
    if "schedule e" not in header_text or "supplemental income and loss" not in header_text:
        return 0
    return 5 if any(line_matches(line, "3", ("rents", "received")) for line in lines) else 3

def _column_positions(blocks: list[dict]) -> dict[str, float]:
    for line in unique_lines(blocks):
        if "income" not in normalized_line_text(line):
            continue
        columns = {normalize(block["text"]).upper(): block["x1"] for block in line if normalize(block["text"]) in {"a", "b", "c"}}
        if columns:
            return columns
    return {}

def _set_addresses(blocks: list[dict], properties: dict[str, ScheduleEProperty]) -> None:
    header_y = line_y(blocks, "1a", ("physical", "address", "property"))
    if header_y is None:
        return
    seen = set()
    for line in unique_lines(blocks):
        if not 0 < line[0]["y1"] - header_y <= 70:
            continue
        column = normalize(line[0]["text"]).upper()
        if column in properties and len(line) > 1:
            raw = " ".join(block["text"] for block in line[1:])
            if (column, raw) in seen:
                continue
            seen.add((column, raw))
            properties[column].address = raw
            properties[column].blocks["address"] = {**merge_blocks(line[1:]), "raw_text": raw}


def _set_fair_rental_days(blocks: list[dict], properties: dict[str, ScheduleEProperty]) -> None:
    for line in unique_lines(blocks):
        column = normalize(line[0]["text"]).upper()
        if column not in properties:
            continue
        values = [block for block in line if parse_float(block["text"]) is not None and block["x1"] > 300]
        if values:
            properties[column].fair_rental_days = parse_float(values[0]["text"])
            properties[column].blocks["fair_rental_days"] = values[0]


def _set_amount_lines(
    blocks: list[dict],
    properties: dict[str, ScheduleEProperty],
    columns: dict[str, float],
) -> None:
    for field_name, (line_number, tokens) in AMOUNT_LINES.items():
        line = find_line(blocks, line_number, tokens)
        if not line:
            continue
        for block in amount_blocks(line, min(columns.values()) - 40):
            column = nearest_column(block, columns)
            value = parse_float(block["text"])
            if column and value is not None:
                setattr(properties[column], field_name, value)
                properties[column].blocks[field_name] = block


def _validate_totals(blocks: list[dict], properties: dict[str, ScheduleEProperty]) -> None:
    for field_name, (line_number, tokens) in TOTAL_LINES.items():
        total_block = line_value(blocks, line_number, tokens)
        total = parse_float(total_block["text"]) if total_block else None
        if total is None:
            continue
        found = round(sum(getattr(prop, field_name) for prop in properties.values()), 2)
        if abs(found - total) > 1.0:
            raise ExtractionFailed(f"Schedule E {line_number} total mismatch")


def _property_fields(prop: ScheduleEProperty, document_id: UUID) -> list[ExtractedField]:
    prefix = f"schedule_e_property_{prop.property_key}"
    fields = []
    if "address" in prop.blocks:
        fields.append(make_text_field(f"{prefix}_address", prop.blocks["address"], document_id))
    for name in ("fair_rental_days", *AMOUNT_LINES.keys()):
        block = prop.blocks.get(name)
        if block:
            fields.append(make_numeric_field(f"{prefix}_{FIELD_SUFFIXES.get(name, name)}", block, document_id))
    return fields


def _first_header(blocks: list[dict] | TaxReturnBlockIndex) -> dict:
    block_index = as_tax_return_index(blocks)
    for line in unique_lines(blocks):
        if "schedule e" in normalized_line_text(line):
            return merge_blocks(line)
    return block_index.blocks[0]


def _total_block(properties: list[ScheduleEProperty], attr: str, name: str) -> dict | None:
    blocks = [prop.blocks[attr] for prop in properties if attr in prop.blocks]
    if not blocks:
        return None
    return {**merge_blocks(blocks), "text": str(sum(getattr(prop, attr) for prop in properties)), "field": name}


def _has_property_income(prop: ScheduleEProperty) -> bool:
    return bool(prop.address or prop.rents_received or prop.total_expenses)
