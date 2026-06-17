from uuid import uuid4

from app.extractors.model_extractor import extract_fields_with_model


class FakeBackend:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.prompt = ""
        self.schema = {}

    def complete_json(self, prompt: str, schema: dict) -> dict:
        self.prompt = prompt
        self.schema = schema
        return self.payload


def test_model_extractor_returns_fields_with_source_refs():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "tax_year": {"value": 2023, "confidence": 0.97, "source_text": "2023"},
                "schedule_c_net_profit": {
                    "value": 94380,
                    "confidence": 0.91,
                    "source_text": "Line 31 94,380",
                },
            }
        }
    )

    fields = extract_fields_with_model(_blocks(), document_id, "tax_return", backend)

    by_name = {field.field: field for field in fields}
    assert by_name["schedule_c_net_profit"].value == 94380
    assert by_name["schedule_c_net_profit"].page == 8
    assert by_name["schedule_c_net_profit"].bounding_box.x1 == 10
    assert by_name["schedule_c_net_profit"].confidence == 0.91
    assert "schedule_c_net_profit" in backend.prompt
    assert "fields" in backend.schema["properties"]


def test_model_extractor_flags_null_without_fabricated_source():
    document_id = uuid4()
    backend = FakeBackend(
        {"fields": {"schedule_c_depreciation": {"value": None, "confidence": 0.4, "source_text": None}}}
    )

    fields = extract_fields_with_model(_blocks(), document_id, "tax_return", backend)

    field = fields[0]
    assert field.value is None
    assert field.page is None
    assert field.bounding_box is None
    assert field.confidence == 0.2


def _blocks():
    return [
        {"text": "2023", "page": 1, "x1": 20, "y1": 10, "x2": 50, "y2": 20},
        {"text": "Line", "page": 8, "x1": 10, "y1": 640, "x2": 30, "y2": 650},
        {"text": "31", "page": 8, "x1": 40, "y1": 640, "x2": 55, "y2": 650},
        {"text": "94,380", "page": 8, "x1": 400, "y1": 640, "x2": 450, "y2": 650},
    ]
