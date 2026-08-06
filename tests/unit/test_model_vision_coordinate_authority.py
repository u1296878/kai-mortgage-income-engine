from uuid import uuid4

from app.extractors.model_vision_extractor import extract_fields_with_vision


class FakeVisionBackend:
    def __init__(self, fields: dict) -> None:
        self.payload = {"fields": fields}

    def complete_json(self, prompt: str, schema: dict, images=None) -> dict:
        return self.payload


def test_source_line_ids_override_model_box():
    fields = extract_fields_with_vision(
        [b"page1", b"page2"],
        _w2_blocks(),
        uuid4(),
        "w2",
        FakeVisionBackend(
            {
                "w2_wages": {
                    "value": 57278.79,
                    "confidence": 0.91,
                    "source_text": "57278.79",
                    "source_line_ids": ["L0001"],
                    "box": [0.1, 0.2, 0.3, 0.25],
                    "page_index": 1,
                }
            }
        ),
        page_numbers=[1, 3],
        page_sizes={1: (600.0, 800.0), 3: (612.0, 792.0)},
    )

    wages = _field(fields, "w2_wages")
    assert wages.page == 1
    assert wages.bounding_box.model_dump() == {"x1": 20.0, "y1": 30.0, "x2": 180.0, "y2": 40.0}
    assert wages.review_flags == []


def test_model_box_only_is_low_confidence_review_context():
    fields = extract_fields_with_vision(
        [b"page"],
        _w2_label_only_blocks(),
        uuid4(),
        "w2",
        FakeVisionBackend(
            {
                "w2_wages": {
                    "value": 57278.79,
                    "confidence": 0.9,
                    "source_text": "unmatched",
                    "box": [0.1, 0.1, 0.3, 0.2],
                    "page_index": 0,
                },
            }
        ),
        page_numbers=[1],
    )

    wages = _field(fields, "w2_wages")
    assert wages.bounding_box is None
    assert wages.confidence == 0.2
    assert _messages(wages) == ["source is model-estimated; verify"]


def _w2_blocks():
    return [
        *_line(1, 10, "2025 Form W-2 Wage and Tax Statement"),
        *_line(1, 30, "1 Wages tips other compensation 57278.79"),
    ]


def _w2_label_only_blocks():
    return [
        *_line(1, 10, "2025 Form W-2 Wage and Tax Statement"),
        *_line(1, 30, "1 Wages tips other compensation"),
    ]


def _line(page: int, y: float, text: str) -> list[dict]:
    blocks = []
    x = 20
    for word in text.split():
        blocks.append({"text": word, "page": page, "x1": x, "y1": y, "x2": x + 10, "y2": y + 10})
        x += 30
    return blocks


def _field(fields, name: str):
    return next(field for field in fields if field.field == name)


def _messages(field) -> list[str]:
    return [flag["message"] for flag in field.review_flags]
