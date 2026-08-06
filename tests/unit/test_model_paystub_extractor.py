from uuid import uuid4

from app.extractors.model_extractor import extract_fields_with_model


class FakeBackend:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.prompts = []

    def complete_json(self, prompt: str, schema: dict) -> dict:
        self.prompts.append(prompt)
        return self.payload


def test_model_paystub_extractor_returns_numeric_and_text_fields():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "paystub_gross_ytd": {"value": 45000, "confidence": 0.92, "source_text": "45,000.00", "source_line_ids": ["L0003"]},
                "paystub_period_end": {"value": None, "confidence": 0.88, "text_value": "2025-06-30", "source_line_ids": ["L0002"]},
                "paystub_employer_name": {"value": None, "confidence": 0.8, "text_value": "Acme Corp", "source_line_ids": ["L0001"]},
            }
        }
    )

    fields = extract_fields_with_model(_paystub_blocks(), document_id, "pay_stub", backend)
    by_name = {field.field: field for field in fields}

    assert by_name["paystub_gross_ytd"].value == 45000
    assert by_name["paystub_gross_ytd"].page == 1
    assert by_name["paystub_period_end"].raw_text == "Period End 2025-06-30"
    assert by_name["paystub_employer_name"].raw_text == "Employer Name Acme Corp"
    assert any("paystub_gross_ytd" in prompt for prompt in backend.prompts)


def _paystub_blocks() -> list[dict]:
    return [
        *_line(1, 10, "Employer Name Acme Corp"),
        *_line(1, 30, "Period End 2025-06-30"),
        *_line(1, 50, "YTD Gross 45,000.00"),
        *_line(1, 70, "Current Gross 3,750.00"),
    ]


def _line(page: int, y: float, text: str) -> list[dict]:
    blocks = []
    x = 20
    for word in text.split():
        width = max(10, len(word) * 5)
        blocks.append({"text": word, "page": page, "x1": x, "y1": y, "x2": x + width, "y2": y + 10})
        x += width + 10
    return blocks
