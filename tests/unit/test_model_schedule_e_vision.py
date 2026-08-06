from uuid import uuid4

from app.extractors.model_vision_extractor import extract_fields_with_vision
from app.services import schedule_e_rental_service
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
        if self.calls == 1:
            return {"fields": {}}
        return {"properties": self.properties}


def test_vision_schedule_e_emits_two_flat_property_field_sets():
    fields = _extract([
        _property("A", "131 E 500 S Provo UT 84606", 22480, 19943, 366),
        _property("B", "2221 Corby Blvd South Bend IN 46615", 13500, 12597, 240),
    ])

    by_name = {field.field: field for field in fields}
    assert by_name["schedule_e_present"].value == 1.0
    assert by_name["schedule_e_property_a_address"].raw_text == "A 131 E 500 S Provo UT 84606"
    assert by_name["schedule_e_property_a_gross_rents"].value == 22480
    assert by_name["schedule_e_property_b_total_expenses"].value == 12597
    assert by_name["schedule_e_gross_rents_total"].value == 35980


def test_vision_schedule_e_single_property_is_consumable_by_rental_service():
    fields = _extract([_property("A", "131 E 500 S Provo UT 84606", 22480, 19943, 366)])

    by_name = {field.field: field for field in fields}
    property_input = schedule_e_rental_service.build_property_input(by_name, "a")

    year = property_input.schedule_e_years[0]
    assert year.months_in_service == 12.0
    assert year.rents_received == 22480
    assert year.total_expenses == 19943


def test_vision_schedule_e_blank_line_items_become_zero():
    fields = _extract([_property("A", "131 E 500 S Provo UT 84606", None, None, 366)])

    by_name = {field.field: field for field in fields}
    assert by_name["schedule_e_property_a_gross_rents"].value == 0.0
    assert by_name["schedule_e_property_a_total_expenses"].value == 0.0


def test_vision_schedule_e_derives_source_from_source_line_ids():
    backend = FakeVisionBackend([_property("A", "131 E 500 S Provo UT 84606", 22480, 19943, 366)])

    fields = _extract_with_backend(backend)

    rents = next(field for field in fields if field.field == "schedule_e_property_a_gross_rents")
    assert rents.page == 2
    assert rents.bounding_box.model_dump() == {"x1": 50.0, "y1": 260.0, "x2": 566.0, "y2": 272.0}
    assert "source_line_ids" in backend.prompts[1]
    assert "[L0008 p2] 3 Rents received 22,480.00 13,500.00" in backend.prompts[1]


def _extract(properties: list[dict]):
    return _extract_with_backend(FakeVisionBackend(properties))


def _extract_with_backend(backend: FakeVisionBackend):
    return extract_fields_with_vision(
        [b"schedule-e-page"],
        schedule_e_blocks(),
        uuid4(),
        "tax_return",
        backend,
        page_numbers=[2],
        page_sizes={2: (630.0, 792.0)},
    )


def _property(column: str, address: str, rents, expenses, days: int) -> dict:
    return {
        "column": column,
        "address": _entry(address, source_text=address, source_line_ids=[_line_id(column, "address")]),
        "fair_rental_days": _entry(days, source_line_ids=[_line_id(column, "days")]),
        "rents_received": _entry(rents, source_line_ids=["L0008"] if rents is not None else []),
        "insurance": _entry(None),
        "mortgage_interest": _entry(None),
        "other_interest": _entry(None),
        "taxes": _entry(None),
        "depreciation_depletion": _entry(None),
        "total_expenses": _entry(expenses, source_line_ids=["L0014"] if expenses is not None else []),
    }


def _entry(value, source_text: str | None = None, source_line_ids: list[str] | None = None) -> dict:
    return {
        "value": value,
        "confidence": 0.9,
        "source_text": source_text or (str(value) if value is not None else None),
        "source_line_ids": source_line_ids or [],
    }


def _line_id(column: str, field: str) -> str:
    ids = {
        ("A", "address"): "L0003",
        ("B", "address"): "L0004",
        ("A", "days"): "L0005",
        ("B", "days"): "L0006",
    }
    return ids[(column, field)]
