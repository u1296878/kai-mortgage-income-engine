from uuid import uuid4

from app.extractors.model_vision_extractor import extract_fields_with_vision


class FakeVisionBackend:
    def __init__(self, fields: dict) -> None:
        self.payload = {"fields": fields}
        self.prompts = []
        self.schemas = []

    def complete_json(self, prompt: str, schema: dict, images=None) -> dict:
        self.prompts.append(prompt)
        self.schemas.append(schema)
        return self.payload


def test_vision_source_box_converts_normalized_coords_to_pdf_points():
    backend = FakeVisionBackend(
        {
            "w2_wages": {
                "value": 1000,
                "confidence": 0.91,
                "source_text": "unmatched",
                "box": [0.1, 0.2, 0.3, 0.25],
                "page_index": 1,
            }
        }
    )

    fields = extract_fields_with_vision(
        [b"page1", b"page2"],
        _w2_blocks(),
        uuid4(),
        "w2",
        backend,
        page_numbers=[1, 3],
        page_sizes={1: (600.0, 800.0), 3: (612.0, 792.0)},
    )

    wages = _field(fields, "w2_wages")
    assert wages.page == 3
    assert wages.bounding_box.model_dump() == {"x1": 61.2, "y1": 158.4, "x2": 183.6, "y2": 198.0}
    assert "normalized 0.0-1.0 coordinates" in backend.prompts[0]
    assert "box" in backend.schemas[0]["properties"]["fields"]["properties"]["w2_wages"]["properties"]


def test_vision_source_box_falls_back_to_ocr_match_when_model_box_missing():
    backend = FakeVisionBackend(
        {
            "w2_wages": {
                "value": 57278.79,
                "confidence": 0.91,
                "source_text": None,
                "box": None,
                "page_index": None,
            }
        }
    )

    fields = extract_fields_with_vision([b"page"], _w2_blocks(), uuid4(), "w2", backend)

    wages = _field(fields, "w2_wages")
    assert wages.page == 1
    assert wages.bounding_box.x1 == 170


def test_vision_source_box_leaves_unlocated_when_model_and_ocr_miss():
    backend = FakeVisionBackend(
        {
            "w2_wages": {
                "value": 57278.79,
                "confidence": 0.91,
                "source_text": "unmatched",
                "box": None,
                "page_index": None,
            }
        }
    )

    fields = extract_fields_with_vision([b"page"], _w2_label_only_blocks(), uuid4(), "w2", backend)

    wages = _field(fields, "w2_wages")
    assert wages.value == 57278.79
    assert wages.page is None
    assert wages.bounding_box is None


def test_vision_source_box_ignores_malformed_model_box_without_crashing():
    backend = FakeVisionBackend(
        {
            "w2_wages": {
                "value": 57278.79,
                "confidence": 0.91,
                "source_text": "unmatched",
                "box": ["bad", 0.2, 0.3, 0.4],
                "page_index": 0,
            }
        }
    )

    fields = extract_fields_with_vision(
        [b"page"],
        _w2_label_only_blocks(),
        uuid4(),
        "w2",
        backend,
        page_numbers=[1],
        page_sizes={1: (612.0, 792.0)},
    )

    assert _field(fields, "w2_wages").bounding_box is None


def test_vision_source_box_clamps_out_of_range_model_coords():
    backend = FakeVisionBackend(
        {
            "w2_wages": {
                "value": 57278.79,
                "confidence": 0.91,
                "source_text": "unmatched",
                "box": [-0.1, 0.2, 1.2, 0.4],
                "page_index": 0,
            }
        }
    )

    fields = extract_fields_with_vision(
        [b"page"],
        _w2_label_only_blocks(),
        uuid4(),
        "w2",
        backend,
        page_numbers=[1],
        page_sizes={1: (612.0, 792.0)},
    )

    assert _field(fields, "w2_wages").bounding_box.model_dump() == {
        "x1": 0.0, "y1": 158.4, "x2": 612.0, "y2": 316.8,
    }


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
