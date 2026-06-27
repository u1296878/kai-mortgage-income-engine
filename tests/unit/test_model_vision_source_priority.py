from uuid import uuid4

from app.extractors.model_vision_extractor import extract_fields_with_vision


class FakeVisionBackend:
    def complete_json(self, prompt: str, schema: dict, images=None) -> dict:
        return {
            "fields": {
                "total_income": {
                    "value": 85247,
                    "confidence": 0.94,
                    "source_text": "85,247",
                    "box": [0.9, 0.1, 1.0, 0.2],
                    "page_index": 0,
                }
            }
        }


def test_vision_source_prefers_ocr_match_over_model_box():
    fields = extract_fields_with_vision(
        [b"page"],
        _tax_return_blocks(),
        uuid4(),
        "tax_return",
        FakeVisionBackend(),
        page_numbers=[1],
        page_sizes={1: (600.0, 800.0)},
    )

    total_income = next(field for field in fields if field.field == "total_income")
    assert total_income.value == 85247
    assert total_income.bounding_box.model_dump() == {
        "x1": 570.0,
        "y1": 600.0,
        "x2": 650.0,
        "y2": 625.0,
    }


def _tax_return_blocks():
    return [
        *_line(1, 10, "Form 1040 2024 U.S. Individual Income Tax Return"),
        *_line(1, 560, "8 Additional income from Schedule 1 line 10 85,247"),
        *_line(1, 600, "9 Add lines 1z through 8 This is your total income 85,247"),
        *_line(1, 640, "11 Adjusted gross income 77,555"),
    ]


def _line(page: int, y: float, text: str) -> list[dict]:
    blocks = []
    x = 20
    for word in text.split():
        width = 80 if "," in word else 10
        blocks.append({"text": word, "page": page, "x1": x, "y1": y, "x2": x + width, "y2": y + 25})
        x += 50
    return blocks
