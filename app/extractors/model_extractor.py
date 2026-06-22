from uuid import UUID

from app.extractors.model_backend import ModelBackend
from app.extractors.model_field_schemas import FEDERAL_FIELDS, SCHEDULE_C_FIELDS, W2_MODEL_FIELDS
from app.extractors.model_field_schemas import descriptions_for_fields, field_descriptions_for
from app.extractors.model_field_schemas import schema_for_fields
from app.extractors.model_prompt import build_prompt, field_context_blocks, tax_return_sections
from app.extractors.model_source_locator import locate_source
from app.extractors.model_value_guard import guarded_value
from app.extractors.model_w2_context import w2_context_blocks
from app.extractors.w2_extractor import _form_blocks as w2_form_blocks
from app.exceptions import ModelExtractionFailed
from app.schemas.extraction import BoundingBox, ExtractedField


def extract_fields_with_model(
    blocks: list[dict],
    document_id: UUID,
    doc_type: str,
    backend: ModelBackend,
) -> list[ExtractedField]:
    field_descriptions_for(doc_type)
    if doc_type == "w2":
        return _extract_group(
            W2_MODEL_FIELDS,
            w2_form_blocks(blocks),
            document_id,
            backend,
            w2_context_blocks,
        )
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
    context_blocks=field_context_blocks,
) -> list[ExtractedField]:
    if not blocks:
        return [_null_field(name, document_id) for name in field_names]
    return [_extract_one_field(name, blocks, document_id, backend, context_blocks) for name in field_names]


def _extract_one_field(
    name: str,
    blocks: list[dict],
    document_id: UUID,
    backend: ModelBackend,
    context_blocks,
) -> ExtractedField:
    field_blocks = context_blocks(name, blocks)
    if not field_blocks:
        return _null_field(name, document_id)
    field_names = (name,)
    response = backend.complete_json(
        build_prompt(descriptions_for_fields(field_names), field_blocks),
        schema_for_fields(field_names),
    )
    payload = _payload_from_response(response)
    return _field_from_model(name, payload.get(name), field_blocks, document_id)


def _payload_from_response(response: dict) -> dict:
    payload = response.get("fields", response)
    if not isinstance(payload, dict):
        raise ModelExtractionFailed("Model extraction payload must be an object")
    return payload


def _field_from_model(
    name: str,
    entry,
    blocks: list[dict],
    document_id: UUID,
) -> ExtractedField:
    value, confidence, source_text = _entry_parts(entry)
    original_value = value
    guarded = guarded_value(name, value, blocks)
    value = guarded.value
    if original_value is None and value is not None:
        confidence = max(confidence, 0.6)
    if value is None:
        confidence = min(confidence, 0.2)
        if original_value is not None:
            source_text = None
    source = locate_source(blocks, value, source_text)
    if source is None:
        return ExtractedField(
            field=name,
            value=value,
            document_id=document_id,
            page=None,
            bounding_box=None,
            raw_text=source_text,
            confidence=min(confidence, 0.2),
            review_flags=guarded.review_flags,
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
        review_flags=guarded.review_flags,
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
    raw_value = entry.get("value") if isinstance(entry, dict) else None
    confidence = entry.get("confidence", 0.8) if isinstance(entry, dict) else 0.0
    source_text = entry.get("source_text") if isinstance(entry, dict) else None
    value = _float_or_none(raw_value)
    if raw_value is not None and value is None:
        source_text = None
    return value, _confidence(confidence), source_text


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
