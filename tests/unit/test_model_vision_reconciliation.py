from uuid import uuid4

from app.extractors.model_vision_extractor import extract_fields_with_vision
from app.services import extraction_validation


class FakeVisionBackend:
    def __init__(self, fields: dict) -> None:
        self.payload = {"fields": fields}

    def complete_json(self, prompt: str, schema: dict, images=None) -> dict:
        return self.payload


def test_vision_reconcile_keeps_model_value_when_ocr_anchor_disagrees():
    backend = FakeVisionBackend(
        {
            "schedule_c_net_profit": {
                "value": 85247,
                "confidence": 0.94,
                "source_text": "85,247",
            },
        }
    )

    fields = extract_fields_with_vision([b"page"], _tax_return_blocks(), uuid4(), "tax_return", backend)

    net_profit = _field(fields, "schedule_c_net_profit")
    issues = extraction_validation.validate_extraction("tax_return", fields)
    assert net_profit.value == 85247
    assert _high_message(issues, "schedule_c_net_profit") == (
        "schedule_c_net_profit: model read 85,247; form line 31 OCR read 1; "
        "used the model value; verify."
    )


def test_vision_reconcile_leaves_agreeing_anchor_unflagged():
    backend = FakeVisionBackend(
        {
            "schedule_c_net_profit": {
                "value": 1,
                "confidence": 0.94,
                "source_text": "1",
            },
        }
    )

    fields = extract_fields_with_vision([b"page"], _tax_return_blocks(), uuid4(), "tax_return", backend)

    issues = extraction_validation.validate_extraction("tax_return", fields)
    assert _field(fields, "schedule_c_net_profit").value == 1
    assert _high_message(issues, "schedule_c_net_profit") is None


def test_vision_arithmetic_cross_checks_still_flag():
    backend = FakeVisionBackend(
        {
            "total_income": {"value": 1000, "confidence": 0.94, "source_text": "1,000"},
            "agi": {"value": 2000, "confidence": 0.94, "source_text": "2,000"},
        }
    )

    fields = extract_fields_with_vision([b"page"], _tax_return_blocks(), uuid4(), "tax_return", backend)

    issues = extraction_validation.validate_extraction("tax_return", fields)
    assert "AGI exceeds total income." in [issue["message"] for issue in issues]


def test_vision_tax_return_label_polluted_miles_cleans_to_null():
    backend = FakeVisionBackend(
        {
            "schedule_c_business_miles": {
                "value": "a Business b Commuting (see instructions) c Other",
                "confidence": 0.9,
                "source_text": "a Business b Commuting (see instructions) c Other",
            },
        }
    )

    fields = extract_fields_with_vision([b"page"], _tax_return_blocks(), uuid4(), "tax_return", backend)

    assert _field(fields, "schedule_c_business_miles").value is None


def test_vision_tax_return_rejects_non_amortization_part_v_amount():
    backend = FakeVisionBackend(
        {
            "schedule_c_amortization_casualty": {
                "value": 1459,
                "confidence": 0.9,
                "source_text": "Telephone 1,459",
            },
        }
    )

    fields = extract_fields_with_vision([b"page"], _tax_return_blocks(), uuid4(), "tax_return", backend)

    assert _field(fields, "schedule_c_amortization_casualty").value is None


def _tax_return_blocks():
    return [
        *_line(1, 10, "Form 1040 2024 U.S. Individual Income Tax Return"),
        *_line(1, 30, "9 Total income 85,247"),
        *_line(1, 50, "11 Adjusted gross income 77,555"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 80, "31 Net profit or loss Line 31 1,"),
        *_line(8, 100, "44a Business b Commuting see instructions c Other"),
        *_line(8, 120, "Part V Other Expenses"),
        *_line(8, 140, "Telephone 1,459"),
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


def _high_message(issues, field_name: str) -> str | None:
    return next(
        (
            issue["message"]
            for issue in issues
            if field_name in issue["fields"] and issue["severity"] == "high"
        ),
        None,
    )
