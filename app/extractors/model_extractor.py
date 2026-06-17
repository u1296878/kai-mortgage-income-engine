from uuid import UUID

from app.extractors.block_utils import line_for_block, merge_blocks
from app.extractors.extracted_field_factory import parse_float
from app.extractors.model_backend import ModelBackend
from app.extractors.model_field_schemas import field_descriptions_for, field_schema_for
from app.exceptions import ModelExtractionFailed
from app.schemas.extraction import BoundingBox, ExtractedField


def extract_fields_with_model(
    blocks: list[dict],
    document_id: UUID,
    doc_type: str,
    backend: ModelBackend,
) -> list[ExtractedField]:
    schema = field_schema_for(doc_type)
    descriptions = field_descriptions_for(doc_type)
    response = backend.complete_json(_prompt(descriptions, blocks), schema)
    payload = response.get("fields", response)
    if not isinstance(payload, dict):
        raise ModelExtractionFailed("Model extraction payload must be an object")
    return [
        _field_from_model(name, payload.get(name), blocks, document_id)
        for name in descriptions
        if name in payload
    ]


def _prompt(descriptions: dict[str, str], blocks: list[dict]) -> str:
    fields = "\n".join(f"- {name}: {description}" for name, description in descriptions.items())
    return (
        "Extract mortgage income document fields from the OCR/text below.\n"
        "Return strict JSON matching the supplied schema. Use numbers only. "
        "When a listed line label and adjacent number are visible, extract that "
        "number and include the exact nearby source_text. If a field is absent "
        "or the visible text is ambiguous, set its value to null. Never compute "
        "income or infer missing values.\n\n"
        f"Fields:\n{fields}\n\nDocument text:\n{_page_text(blocks)}"
    )


def _page_text(blocks: list[dict]) -> str:
    pages = sorted({block["page"] for block in blocks})
    sections = []
    for page in pages:
        words = sorted(
            (block for block in blocks if block["page"] == page),
            key=lambda block: (block["y1"], block["x1"]),
        )
        text = " ".join(block["text"] for block in words)
        sections.append(f"[page {page}]\n{text}")
    return "\n\n".join(sections)


def _field_from_model(
    name: str,
    entry,
    blocks: list[dict],
    document_id: UUID,
) -> ExtractedField:
    value, confidence, source_text = _entry_parts(entry)
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
