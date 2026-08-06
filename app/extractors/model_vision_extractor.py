from uuid import UUID

from app.extractors.model_backend import ModelBackend
from app.extractors.model_extractor import _field_from_model, _payload_from_response
from app.extractors.model_field_schemas import descriptions_for_fields, field_descriptions_for
from app.extractors.model_field_schemas import schema_for_fields
from app.extractors.model_prompt import field_context_blocks, page_text, tax_return_sections
from app.extractors.model_schedule_e_vision import extract_schedule_e_with_vision
from app.extractors.model_vision_value_cleaner import clean_vision_entry
from app.extractors.model_w2_context import w2_context_blocks
from app.extractors.w2_extractor import _form_blocks as w2_form_blocks
from app.schemas.extraction import BoundingBox, ExtractedField


def extract_fields_with_vision(
    image_pages: list[bytes],
    blocks: list[dict],
    document_id: UUID,
    doc_type: str,
    backend: ModelBackend,
    page_numbers: list[int] | None = None,
    page_sizes: dict[int, tuple[float, float]] | None = None,
) -> list[ExtractedField]:
    field_names = tuple(field_descriptions_for(doc_type))
    group_blocks = _vision_blocks(blocks, doc_type)
    ordered_pages = page_numbers or sorted({block["page"] for block in group_blocks})
    response = backend.complete_json(
        _vision_prompt(descriptions_for_fields(field_names), group_blocks),
        schema_for_fields(field_names, include_source_box=True, include_source_line_ids=False),
        images=image_pages,
    )
    payload = _payload_from_response(response)
    fields = [
        _field_from_vision(
            name,
            clean_vision_entry(name, payload.get(name)),
            _field_blocks(name, group_blocks, doc_type),
            document_id,
            ordered_pages,
            page_sizes or {},
        )
        for name in field_names
    ]
    if doc_type == "tax_return":
        fields.extend(extract_schedule_e_with_vision(image_pages, blocks, document_id, backend, ordered_pages, page_sizes or {}))
    return fields


def _vision_blocks(blocks: list[dict], doc_type: str) -> list[dict]:
    if doc_type == "w2":
        return w2_form_blocks(blocks)
    if doc_type == "pay_stub":
        return blocks
    sections = tax_return_sections(blocks)
    return [*sections["federal"], *sections["schedule_c"]]


def _field_blocks(name: str, blocks: list[dict], doc_type: str) -> list[dict]:
    if doc_type == "w2":
        return w2_context_blocks(name, blocks) or blocks
    if doc_type == "pay_stub":
        return field_context_blocks(name, blocks) or blocks
    return field_context_blocks(name, blocks) or blocks


def _vision_prompt(descriptions: dict[str, str], blocks: list[dict]) -> str:
    pages = ", ".join(str(page) for page in sorted({block["page"] for block in blocks}))
    return (
        "Extract mortgage income document fields from the attached page images. "
        "Use the OCR text only as page and source-position context. Return strict "
        "JSON matching the supplied schema. Use numbers only, with no dollar signs "
        "or commas. Return only the field value, never a box number, field label, "
        "or description. Numeric example: good w2_wages=57278.79; bad "
        "w2_wages='1 Wages, tips, other compensation 57278.79'. Tax year example: "
        "good tax_year=2025; bad tax_year='W-2 Wage and Tax Statement 2025'. "
        "If a value is not visible, set it to null. Never compute income or infer "
        "missing values. For each visible field, also return box=[x0,y0,x1,y1] "
        "as normalized 0.0-1.0 coordinates around the value on the page image, "
        "plus zero-based page_index in the attached image order. These boxes are "
        "approximate review regions; use null when you cannot place one.\n\n"
        f"Image page order: {pages or 'unknown'}.\n\n"
        f"Fields:\n{_field_list(descriptions)}\n\nOCR text:\n{page_text(blocks)}"
    )


def _field_list(descriptions: dict[str, str]) -> str:
    return "\n".join(f"- {name}: {description}" for name, description in descriptions.items())


def _field_from_vision(
    name: str,
    entry,
    blocks: list[dict],
    document_id: UUID,
    page_numbers: list[int],
    page_sizes: dict[int, tuple[float, float]],
) -> ExtractedField:
    field = _field_from_model(
        name,
        entry,
        blocks,
        document_id,
        preserve_confidence_without_source=True,
        prefer_model_on_mismatch=True,
    )
    if field.page is not None and field.bounding_box is not None:
        return field
    model_source = _model_source(entry, page_numbers, page_sizes)
    if model_source is None:
        return field
    field.page = model_source["page"]
    field.bounding_box = BoundingBox(
        x1=model_source["x1"],
        y1=model_source["y1"],
        x2=model_source["x2"],
        y2=model_source["y2"],
    )
    return field


def _model_source(
    entry,
    page_numbers: list[int],
    page_sizes: dict[int, tuple[float, float]],
) -> dict | None:
    if not isinstance(entry, dict):
        return None
    page = _model_page(entry, page_numbers)
    box = _normalized_box(entry.get("box"))
    if page is None or box is None or page not in page_sizes:
        return None
    width, height = page_sizes[page]
    x0, y0, x1, y1 = box
    return {
        "page": page,
        "x1": round(x0 * width, 2),
        "y1": round(y0 * height, 2),
        "x2": round(x1 * width, 2),
        "y2": round(y1 * height, 2),
    }


def _model_page(entry: dict, page_numbers: list[int]) -> int | None:
    if not page_numbers:
        return None
    page_index = entry.get("page_index")
    if page_index is None and len(page_numbers) == 1:
        return page_numbers[0]
    if isinstance(page_index, int) and 0 <= page_index < len(page_numbers):
        return page_numbers[page_index]
    return None


def _normalized_box(box) -> tuple[float, float, float, float] | None:
    if not isinstance(box, list | tuple) or len(box) != 4:
        return None
    try:
        x0, y0, x1, y1 = (float(value) for value in box)
    except (TypeError, ValueError):
        return None
    x0, y0, x1, y1 = (_clamp(value) for value in (x0, y0, x1, y1))
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
