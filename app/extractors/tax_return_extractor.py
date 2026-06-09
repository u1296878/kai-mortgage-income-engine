from uuid import UUID

from app.exceptions import ExtractionFailed
from app.extractors.tax_return_block_index import TaxReturnBlockIndex
from app.extractors.extracted_field_factory import make_field, make_numeric_field
from app.extractors.tax_return_locator import (
    federal_form_pages,
    find_filing_status,
    find_tax_year,
    line_anchors,
    nearest_money_value,
    schedule_c_pages,
)
from app.extractors.tax_return_patterns import LINE_FIELDS
from app.extractors.schedule_c_extractor import extract_schedule_c_fields
from app.extractors.schedule_e_extractor import extract_schedule_e_fields
from app.schemas.extraction import ExtractedField


def extract_tax_return_fields(blocks: list[dict], document_id: UUID) -> list[ExtractedField]:
    index = TaxReturnBlockIndex(blocks)
    federal_pages = federal_form_pages(index)
    c_pages = schedule_c_pages(index)
    fields: list[ExtractedField] = []

    for field_name, (line_number, tokens) in LINE_FIELDS.items():
        value = _extract_line_value(index, line_number, tokens, federal_pages)
        if value:
            fields.append(make_numeric_field(field_name, value, document_id))

    schedule_c = _extract_line_value(index, "31", ("net", "profit"), c_pages) if c_pages else None
    tax_year = find_tax_year(index, federal_pages)
    filing_status = find_filing_status(index, federal_pages)

    if schedule_c:
        fields.append(make_numeric_field("schedule_c_net", schedule_c, document_id))
    fields.extend(extract_schedule_c_fields(index, document_id, c_pages))
    fields.extend(extract_schedule_e_fields(index, document_id))
    if tax_year:
        fields.append(make_numeric_field("tax_year", tax_year, document_id))
    if filing_status:
        fields.append(make_field("filing_status", 0.0, filing_status, document_id, filing_status["raw_text"]))
    if not {field.field for field in fields} & {"agi", "total_income", "wages"}:
        raise ExtractionFailed("No Form 1040 income fields found")
    return fields


def _extract_line_value(
    blocks: TaxReturnBlockIndex,
    line_number: str,
    tokens: tuple[str, ...],
    pages: set[int] | None = None,
) -> dict | None:
    values = [
        value
        for label in line_anchors(blocks, line_number, tokens, pages)
        if (value := nearest_money_value(label, blocks, line_number)) is not None
    ]
    return values[0] if values else None
