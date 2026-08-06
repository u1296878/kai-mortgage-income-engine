from uuid import UUID

from app.extractors.extracted_field_factory import parse_float
from app.extractors.model_backend import ModelBackend
from app.extractors.model_schedule_e_schema import schedule_e_prompt, schedule_e_schema
from app.extractors.model_source_citations import resolve_model_source
from app.extractors.schedule_e_extractor import schedule_e_pages
from app.extractors.source_lines import SourceLine, build_source_lines
from app.extractors.tax_return_block_index import TaxReturnBlockIndex
from app.schemas.extraction import BoundingBox, ExtractedField

FIELDS = (
    "address",
    "fair_rental_days",
    "rents_received",
    "insurance",
    "mortgage_interest",
    "other_interest",
    "taxes",
    "depreciation_depletion",
    "total_expenses",
)
SUFFIXES = {"rents_received": "gross_rents"}
PROPERTY_KEYS = ("a", "b", "c")


def extract_schedule_e_with_vision(
    image_pages: list[bytes],
    blocks: list[dict],
    document_id: UUID,
    backend: ModelBackend,
    page_numbers: list[int],
    page_sizes: dict[int, tuple[float, float]],
) -> list[ExtractedField]:
    schedule_blocks = _schedule_e_blocks(blocks)
    if not schedule_blocks:
        return []
    source_lines = build_source_lines(schedule_blocks)
    response = backend.complete_json(
        schedule_e_prompt(schedule_blocks, source_lines),
        schedule_e_schema(),
        images=image_pages,
    )
    properties = response.get("properties", [])
    if not isinstance(properties, list):
        return []
    fields = [_field("schedule_e_present", 1.0, document_id, None, "Schedule E")]
    for index, prop in enumerate(properties):
        fields.extend(_property_fields(prop, index, document_id, schedule_blocks, source_lines))
    fields.extend(_gross_rents_total(fields, document_id))
    return fields


def _schedule_e_blocks(blocks: list[dict]) -> list[dict]:
    index = TaxReturnBlockIndex(blocks)
    pages = schedule_e_pages(index)
    return [block for page in sorted(pages) for block in index.page_blocks(page)]


def _property_fields(
    prop,
    index: int,
    document_id: UUID,
    blocks: list[dict],
    source_lines: list[SourceLine],
) -> list[ExtractedField]:
    if not isinstance(prop, dict):
        return []
    key = _property_key(prop, index)
    prefix = f"schedule_e_property_{key}"
    fields = []
    for name in FIELDS:
        entry = prop.get(name)
        if name == "address":
            text = _text(entry)
            if text:
                fields.append(_field(f"{prefix}_address", 0.0, document_id, entry, text, blocks, source_lines, None))
            continue
        suffix = SUFFIXES.get(name, name)
        value = _number(entry)
        fields.append(_field(f"{prefix}_{suffix}", value, document_id, entry, None, blocks, source_lines, _entry_number(entry)))
    return fields


def _field(
    name: str,
    value: float,
    document_id: UUID,
    entry,
    raw_text: str | None = None,
    blocks: list[dict] | None = None,
    source_lines: list[SourceLine] | None = None,
    citation_value: float | None = None,
) -> ExtractedField:
    source_text = raw_text or _text(entry)
    confidence = _confidence(entry)
    if entry is None:
        return ExtractedField(
            field=name,
            value=value,
            document_id=document_id,
            page=None,
            bounding_box=None,
            raw_text=source_text,
            confidence=confidence,
        )
    citation = resolve_model_source(
        name,
        entry,
        source_lines or [],
        blocks or [],
        citation_value,
        source_text,
        confidence,
    )
    source = citation.source
    return ExtractedField(
        field=name,
        value=value,
        document_id=document_id,
        page=source["page"] if source else None,
        bounding_box=_box(source) if source else None,
        raw_text=(source.get("raw_text") if source else None) or source_text,
        confidence=citation.confidence,
        review_flags=citation.review_flags,
    )


def _box(source: dict) -> BoundingBox:
    return BoundingBox(
        x1=round(source["x1"], 2),
        y1=round(source["y1"], 2),
        x2=round(source["x2"], 2),
        y2=round(source["y2"], 2),
    )


def _property_key(prop: dict, index: int) -> str:
    column = str(prop.get("column", "")).lower()
    return column if column in PROPERTY_KEYS else PROPERTY_KEYS[min(index, len(PROPERTY_KEYS) - 1)]


def _number(entry) -> float:
    value = _entry_number(entry)
    return value if value is not None else 0.0


def _entry_number(entry) -> float | None:
    if isinstance(entry, dict):
        value = entry.get("value")
        if value is None:
            value = entry.get("source_text")
    else:
        value = entry
    return parse_float(str(value)) if value is not None else None


def _text(entry) -> str | None:
    if not isinstance(entry, dict):
        return str(entry) if entry else None
    value = entry.get("source_text") or entry.get("text_value") or entry.get("value")
    return str(value) if value else None


def _confidence(entry) -> float:
    if not isinstance(entry, dict):
        return 0.8
    value = parse_float(str(entry.get("confidence", "")))
    return max(0.0, min(1.0, value)) if value is not None else 0.8


def _gross_rents_total(fields: list[ExtractedField], document_id: UUID) -> list[ExtractedField]:
    total = sum(field.value or 0.0 for field in fields if field.field.endswith("_gross_rents"))
    return [_field("schedule_e_gross_rents_total", total, document_id, None)] if total else []
