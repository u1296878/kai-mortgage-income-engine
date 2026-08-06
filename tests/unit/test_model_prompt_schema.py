from app.extractors.model_field_schemas import schema_for_fields
from app.extractors.model_prompt import build_prompt


def test_model_prompt_uses_backend_source_line_ids():
    prompt = build_prompt(
        {"agi": "Form 1040 adjusted gross income."},
        [
            _block("11", 1, 20, 40),
            _block("Adjusted", 1, 40, 40),
            _block("gross", 1, 90, 40),
            _block("income", 1, 130, 40),
            _block("87,638", 1, 180, 40),
        ],
    )

    assert "source_line_ids" in prompt
    assert "Do not invent IDs or return coordinates" in prompt
    assert "Source lines:" in prompt
    assert "[L0001 p1] 11 Adjusted gross income 87,638" in prompt
    assert "[page 1]" not in prompt


def test_model_schema_requires_source_line_ids():
    schema = schema_for_fields(("agi",))

    field_schema = schema["properties"]["fields"]["properties"]["agi"]
    assert "source_line_ids" in field_schema["required"]
    assert field_schema["properties"]["source_line_ids"] == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert "box" not in field_schema["properties"]
    assert "page_index" not in field_schema["properties"]


def test_model_vision_schema_keeps_box_contract_without_source_line_ids():
    schema = schema_for_fields(("agi",), include_source_box=True, include_source_line_ids=False)

    field_schema = schema["properties"]["fields"]["properties"]["agi"]
    assert "source_line_ids" not in field_schema["required"]
    assert "source_line_ids" not in field_schema["properties"]
    assert "box" in field_schema["properties"]
    assert "page_index" in field_schema["properties"]


def _block(text: str, page: int, x1: float, y1: float) -> dict:
    return {"text": text, "page": page, "x1": x1, "y1": y1, "x2": x1 + 10, "y2": y1 + 10}
