from uuid import UUID

from app.extractors.block_utils import line_for_block, merge_blocks
from app.extractors.extracted_field_factory import parse_float
from app.extractors.model_backend import ModelBackend
from app.extractors.model_field_schemas import (
    FEDERAL_FIELDS,
    SCHEDULE_C_FIELDS,
    descriptions_for_fields,
    field_descriptions_for,
    schema_for_fields,
)
from app.extractors.model_prompt import build_prompt, field_context_blocks, tax_return_sections
from app.extractors.model_value_guard import corrected_value
from app.exceptions import ModelExtractionFailed
from app.schemas.extraction import BoundingBox, ExtractedField


def extract_fields_with_model(
    blocks: list[dict],
    document_id: UUID,
    doc_type: str,
    backend: ModelBackend,
) -> list[ExtractedField]:
    field_descriptions_for(doc_type)
    sections = tax_return_sections(blocks)
    return [
        *_extract_group(FEDERAL_FIELDS, sections["federal"], document_id, backend),
        *_extract_group(SCHEDULE_C_FIELDS, sections["schedule_c"], document_id, backend),
    ]


def _extract_group(
    field_names: tuple[str, ...],
    blocks: list[dict],
    document_id: UUID,
    backend: ModelBackend,
) -> list[ExtractedField]:
    if not blocks:
        return [_null_field(name, document_id) for name in field_names]
    return [_extract_one_field(name, blocks, document_id, backend) for name in field_names]


def _extract_one_field(
    name: str,
    blocks: list[dict],
    document_id: UUID,
    backend: ModelBackend,
) -> ExtractedField:
    field_blocks = field_context_blocks(name, blocks)
    if not field_blocks:
        return _null_field(name, document_id)
    field_names = (name,)
    response = backend.complete_json(
        build_prompt(descriptions_for_fields(field_names), field_blocks),
        schema_for_fields(field_names),
    )
    payload = response.get("fields", response)
    if not isinstance(payload, dict):
        raise ModelExtractionFailed("Model extraction payload must be an object")
    return _field_from_model(name, payload.get(name), field_blocks, document_id)


def _field_from_model(
    name: str,
    entry,
    blocks: list[dict],
    document_id: UUID,
) -> ExtractedField:
    value, confidence, source_text = _entry_parts(entry)
    original_value = value
    value = corrected_value(name, value, blocks)
    if original_value is None and value is not None:
        confidence = max(confidence, 0.6)
    if value is None:
        confidence = min(confidence, 0.2)
        if original_value is not None:
            source_text = None
    source = _locate_source(blocks, value, source_text)
    if source is None:
        return ExtractedField(
            field=name,
            value=value,
            document_id=document_id,
            page=None,
            bounding_box=None,
            raw_text=source_text,
            confidence=min(confidence, 0.2),
        )
    return ExtractedField(
        field=name,
        value=value,
        document_id=document_id,
        page=source["page"],
        bounding_box=BoundingBox(
            x1=source["x1"],
            y1=source["y1"],
            x2=source["x2"],
            y2=source["y2"],
        ),
        raw_text=source.get("raw_text", source["text"]),
        confidence=confidence,
    )


def _null_field(name: str, document_id: UUID) -> ExtractedField:
    return ExtractedField(
        field=name,
        value=None,
        document_id=document_id,
        page=None,
        bounding_box=None,
        confidence=0.0,
    )


def _entry_parts(entry) -> tuple[float | None, float, str | None]:
    if entry is None:
        return None, 0.0, None
    if isinstance(entry, int | float):
        return float(entry), 0.8, None
    value = entry.get("value") if isinstance(entry, dict) else None
    confidence = entry.get("confidence", 0.8) if isinstance(entry, dict) else 0.0
    source_text = entry.get("source_text") if isinstance(entry, dict) else None
    return _float_or_none(value), _confidence(confidence), source_text


def _locate_source(
    blocks: list[dict],
    value: float | None,
    source_text: str | None,
) -> dict | None:
    if source_text:
        if source := _find_text_source(blocks, source_text):
            return source
    if value is None:
        return None
    return next(
        (block for block in blocks if _same_number(parse_float(block["text"]), value)),
        None,
    )


def _find_text_source(blocks: list[dict], source_text: str) -> dict | None:
    needle = source_text.lower()
    for block in blocks:
        line = line_for_block(blocks, block)
        text = " ".join(word["text"] for word in line).lower()
        if needle in text:
            return {**merge_blocks(line), "raw_text": source_text}
    return None


def _float_or_none(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _confidence(value) -> float:
    numeric = _float_or_none(value)
    if numeric is None:
        return 0.8
    return max(0.0, min(1.0, numeric))


def _same_number(left: float | None, right: float) -> bool:
    return left is not None and abs(left - right) < 0.01
