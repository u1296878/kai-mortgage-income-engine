from uuid import UUID

from app.extractors.model_backend import ModelBackend
from app.extractors.model_extractor import _field_from_model, _payload_from_response
from app.extractors.model_field_schemas import descriptions_for_fields, field_descriptions_for
from app.extractors.model_field_schemas import schema_for_fields
from app.extractors.model_prompt import field_context_blocks, page_text, tax_return_sections
from app.extractors.model_vision_value_cleaner import clean_vision_entry
from app.extractors.model_w2_context import w2_context_blocks
from app.extractors.w2_extractor import _form_blocks as w2_form_blocks
from app.schemas.extraction import ExtractedField


def extract_fields_with_vision(
    image_pages: list[bytes],
    blocks: list[dict],
    document_id: UUID,
    doc_type: str,
    backend: ModelBackend,
) -> list[ExtractedField]:
    field_names = tuple(field_descriptions_for(doc_type))
    group_blocks = _vision_blocks(blocks, doc_type)
    response = backend.complete_json(
        _vision_prompt(descriptions_for_fields(field_names), group_blocks),
        schema_for_fields(field_names),
        images=image_pages,
    )
    payload = _payload_from_response(response)
    return [
        _field_from_model(
            name,
            clean_vision_entry(name, payload.get(name)),
            _field_blocks(name, group_blocks, doc_type),
            document_id,
        )
        for name in field_names
    ]


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
        "missing values.\n\n"
        f"Image page order: {pages or 'unknown'}.\n\n"
        f"Fields:\n{_field_list(descriptions)}\n\nOCR text:\n{page_text(blocks)}"
    )


def _field_list(descriptions: dict[str, str]) -> str:
    return "\n".join(f"- {name}: {description}" for name, description in descriptions.items())
