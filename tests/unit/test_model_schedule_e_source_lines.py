from uuid import uuid4

from app.extractors.model_schedule_e_schema import FIELD_NAMES, schedule_e_prompt, schedule_e_schema
from app.extractors.model_vision_extractor import extract_fields_with_vision
from tests.unit.test_schedule_e_extractor import schedule_e_blocks


class FakeVisionBackend:
    def __init__(self, properties: list[dict]) -> None:
        self.calls = 0
        self.properties = properties
        self.prompts = []
        self.schemas = []

    def complete_json(self, prompt: str, schema: dict, images=None) -> dict:
        self.calls += 1
        self.prompts.append(prompt)
        self.schemas.append(schema)
        return {"fields": {}} if self.calls == 1 else {"properties": self.properties}


def test_schedule_e_prompt_uses_source_line_contract():
    prompt = schedule_e_prompt(schedule_e_blocks())

    assert "source_line_ids" in prompt
    assert "Do not invent source IDs or return coordinates" in prompt
    assert "[L0008 p2] 3 Rents received 22,480.00 13,500.00" in prompt
    assert "source_line_ids []" in prompt


def test_schedule_e_schema_requires_nested_source_line_ids():
    schema = schedule_e_schema()

    field_schema = schema["properties"]["properties"]["items"]["properties"]["rents_received"]
    assert field_schema["required"] == ["value", "confidence", "source_text", "source_line_ids"]
    assert field_schema["properties"]["source_line_ids"] == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert "box" not in field_schema["properties"]
    assert "page_index" not in field_schema["properties"]


def test_schedule_e_multiple_properties_keep_source_references():
    fields = _extract([
        _property("A", rents_entry=_entry(22480, "22,480.00", ["L0008"])),
        _property("B", rents_entry=_entry(13500, "13,500.00", ["L0008"])),
    ])

    by_name = {field.field: field for field in fields}
    assert by_name["schedule_e_property_a_gross_rents"].value == 22480
    assert by_name["schedule_e_property_b_gross_rents"].value == 13500
    assert by_name["schedule_e_property_a_gross_rents"].bounding_box.y1 == 260
    assert by_name["schedule_e_property_b_gross_rents"].raw_text == "3 Rents received 22,480.00 13,500.00"


def test_schedule_e_invalid_id_flags_only_that_property_field():
    fields = _extract([
        _property("A", rents_entry=_entry(22480, "22,480.00", ["L0008"])),
        _property("B", rents_entry=_entry(13500, "13,500.00", ["L9999"])),
    ])

    by_name = {field.field: field for field in fields}
    assert _messages(by_name["schedule_e_property_a_gross_rents"]) == []
    assert _messages(by_name["schedule_e_property_b_gross_rents"]) == ["source_line_ids invalid: L9999"]
    assert by_name["schedule_e_property_b_gross_rents"].confidence == 0.2


def test_schedule_e_missing_id_falls_back_with_review_flags():
    field = _gross_rents_field(_entry(22480, "22,480.00"))

    assert field.page == 2
    assert field.confidence == 0.2
    assert _messages(field) == [
        "source_line_ids missing for model value",
        "source located by fallback; verify",
    ]


def test_schedule_e_source_text_mismatch_is_flagged():
    field = _gross_rents_field(_entry(22480, "wrong text", ["L0008"]))

    assert field.page == 2
    assert field.confidence == 0.2
    assert _messages(field) == ["source_text not found in cited source"]


def test_schedule_e_numeric_value_mismatch_is_flagged():
    field = _gross_rents_field(_entry(99999, "22,480.00", ["L0008"]))

    assert field.page == 2
    assert field.confidence == 0.2
    assert _messages(field) == ["value not found in cited source"]


def _gross_rents_field(entry):
    fields = _extract([_property("A", rents_entry=entry)])
    return next(field for field in fields if field.field == "schedule_e_property_a_gross_rents")


def _extract(properties: list[dict]):
    return extract_fields_with_vision(
        [b"page"],
        schedule_e_blocks(),
        uuid4(),
        "tax_return",
        FakeVisionBackend(properties),
        page_numbers=[2],
        page_sizes={2: (630.0, 792.0)},
    )


def _property(column: str, rents_entry: dict) -> dict:
    return {
        "column": column,
        **{name: _entry(None, None, []) for name in FIELD_NAMES},
        "rents_received": rents_entry,
    }


def _entry(value, source_text: str | None = None, source_line_ids: list[str] | None = None) -> dict:
    return {
        "value": value,
        "confidence": 0.9,
        "source_text": source_text,
        "source_line_ids": source_line_ids if source_line_ids is not None else [],
    }


def _messages(field):
    return [flag["message"] for flag in field.review_flags]
