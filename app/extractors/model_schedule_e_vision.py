from uuid import UUID

from app.extractors.extracted_field_factory import parse_float
from app.extractors.model_backend import ModelBackend
from app.extractors.model_schedule_e_schema import schedule_e_prompt, schedule_e_schema
from app.extractors.schedule_e_extractor import schedule_e_pages
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
    response = backend.complete_json(
        schedule_e_prompt(schedule_blocks),
        schedule_e_schema(),
        images=image_pages,
    )
    properties = response.get("properties", [])
    if not isinstance(properties, list):
        return []
    fields = [_field("schedule_e_present", 1.0, document_id, None, "Schedule E")]
    for index, prop in enumerate(properties):
        fields.extend(_property_fields(prop, index, document_id, page_numbers, page_sizes))
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
    page_numbers: list[int],
    page_sizes: dict[int, tuple[float, float]],
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
                fields.append(_field(f"{prefix}_address", 0.0, document_id, entry, text, page_numbers, page_sizes))
            continue
        suffix = SUFFIXES.get(name, name)
        fields.append(_field(f"{prefix}_{suffix}", _number(entry), document_id, entry, None, page_numbers, page_sizes))
    return fields


def _field(
    name: str,
    value: float,
    document_id: UUID,
    entry,
    raw_text: str | None = None,
    page_numbers: list[int] | None = None,
    page_sizes: dict[int, tuple[float, float]] | None = None,
) -> ExtractedField:
    source = _source(entry, page_numbers or [], page_sizes or {})
    return ExtractedField(
        field=name,
        value=value,
        document_id=document_id,
        page=source["page"] if source else None,
        bounding_box=_box(source) if source else None,
        raw_text=raw_text or _text(entry),
        confidence=_confidence(entry),
    )


def _source(entry, page_numbers: list[int], page_sizes: dict[int, tuple[float, float]]) -> dict | None:
    if not isinstance(entry, dict):
        return None
    page_index = entry.get("page_index")
    if page_index is None and len(page_numbers) == 1:
        page_index = 0
    if not isinstance(page_index, int) or not 0 <= page_index < len(page_numbers):
        return None
    page = page_numbers[page_index]
    box = _normalized_box(entry.get("box"))
    if box is None or page not in page_sizes:
        return None
    width, height = page_sizes[page]
    x0, y0, x1, y1 = box
    return {"page": page, "x1": x0 * width, "y1": y0 * height, "x2": x1 * width, "y2": y1 * height}


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
    if isinstance(entry, dict):
        value = entry.get("value")
        if value is None:
            value = entry.get("source_text")
    else:
        value = entry
    return parse_float(str(value)) if value is not None and parse_float(str(value)) is not None else 0.0


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


def _normalized_box(box) -> tuple[float, float, float, float] | None:
    if not isinstance(box, list | tuple) or len(box) != 4:
        return None
    try:
        x0, y0, x1, y1 = (_clamp(float(value)) for value in box)
    except (TypeError, ValueError):
        return None
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
