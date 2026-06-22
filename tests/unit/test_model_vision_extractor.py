from uuid import uuid4

from app.extractors.model_vision_extractor import extract_fields_with_vision


class FakeVisionBackend:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.prompts = []
        self.schemas = []
        self.images = []

    def complete_json(self, prompt: str, schema: dict, images=None) -> dict:
        self.prompts.append(prompt)
        self.schemas.append(schema)
        self.images.append(images)
        return self.payload


def test_vision_extractor_returns_fields_with_located_source_refs():
    document_id = uuid4()
    backend = FakeVisionBackend(
        {
            "fields": {
                "tax_year": {"value": 2023, "confidence": 0.97, "source_text": "2023"},
                "total_income": {"value": 94380, "confidence": 0.92, "source_text": "94,380"},
                "agi": {"value": 87638, "confidence": 0.92, "source_text": "87,638"},
                "schedule_c_net_profit": {
                    "value": 94380,
                    "confidence": 0.91,
                    "source_text": "Line 31 94,380",
                },
            }
        }
    )

    fields = extract_fields_with_vision([b"page"], _blocks(), document_id, "tax_return", backend)

    by_name = {field.field: field for field in fields}
    assert by_name["schedule_c_net_profit"].value == 94380
    assert by_name["schedule_c_net_profit"].page == 8
    assert by_name["schedule_c_net_profit"].bounding_box.x1 == 230
    assert backend.images == [[b"page"]]
    assert "Image page order: 1, 8" in backend.prompts[0]


def _blocks():
    return [
        *_line(1, 10, "Form 1040 2023 U.S. Individual Income Tax Return"),
        *_line(1, 30, "9 Total income 94,380"),
        *_line(1, 50, "11 Adjusted gross income 87,638"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 80, "31 Net profit or loss Line 31 94,380"),
    ]


def _line(page: int, y: float, text: str) -> list[dict]:
    blocks = []
    x = 20
    for word in text.split():
        blocks.append({"text": word, "page": page, "x1": x, "y1": y, "x2": x + 10, "y2": y + 10})
        x += 30
    return blocks
