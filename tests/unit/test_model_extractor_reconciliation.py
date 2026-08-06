from uuid import uuid4

from app.extractors.model_extractor import extract_fields_with_model
from app.services import extraction_validation


class FakeBackend:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def complete_json(self, prompt: str, schema: dict) -> dict:
        return self.payload


def test_model_extractor_reconciles_net_profit_against_form_line():
    backend = FakeBackend(
        {"fields": {"schedule_c_net_profit": _entry(1, "Line 31 85,247", ["L0001"])}}
    )

    fields = extract_fields_with_model(_mismatched_net_profit_blocks(), uuid4(), "tax_return", backend)

    net_profit = _field(fields, "schedule_c_net_profit")
    issues = extraction_validation.validate_extraction("tax_return", fields)
    high_issue = next(issue for issue in issues if issue["severity"] == "high")
    assert net_profit.value == 85247
    assert net_profit.raw_text == "31 Net profit or loss Line 31 85,247"
    assert extraction_validation.has_high_issue(issues)
    assert high_issue == {
        "fields": ["schedule_c_net_profit"],
        "message": "schedule_c_net_profit: model read 1 but Form line 31 shows 85,247; used the form value; verify.",
        "severity": "high",
    }


def test_model_extractor_keeps_agreeing_anchor_clean():
    backend = FakeBackend(
        {"fields": {"schedule_c_net_profit": _entry(94380, "Line 31 94,380", ["L0001"])}}
    )

    fields = extract_fields_with_model(_blocks(), uuid4(), "tax_return", backend)

    issues = extraction_validation.validate_extraction("tax_return", fields)
    assert _field(fields, "schedule_c_net_profit").value == 94380
    assert not any("model read" in issue["message"] for issue in issues)


def test_model_extractor_keeps_model_value_when_anchor_missing():
    backend = FakeBackend(
        {"fields": {"schedule_c_net_profit": _entry(50000, None, None)}}
    )

    fields = extract_fields_with_model(_missing_net_profit_anchor_blocks(), uuid4(), "tax_return", backend)

    issues = extraction_validation.validate_extraction("tax_return", fields)
    assert _field(fields, "schedule_c_net_profit").value == 50000
    assert not any("model read" in issue["message"] for issue in issues)


def _entry(value: float, source_text: str | None, source_line_ids: list[str] | None) -> dict:
    entry = {"value": value, "confidence": 0.95, "source_text": source_text}
    if source_line_ids is not None:
        entry["source_line_ids"] = source_line_ids
    return entry


def _blocks():
    return [
        *_line(1, 10, "Form 1040 2023 U.S. Individual Income Tax Return"),
        *_line(1, 30, "9 Total income 94,380"),
        *_line(1, 50, "11 Adjusted gross income 87,638"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 80, "31 Net profit or loss Line 31 94,380"),
    ]


def _mismatched_net_profit_blocks():
    return [
        *_line(1, 10, "Form 1040 2024 U.S. Individual Income Tax Return"),
        *_line(1, 30, "9 Total income 85,247"),
        *_line(1, 50, "11 Adjusted gross income 85,247"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 80, "31 Net profit or loss Line 31 85,247"),
    ]


def _missing_net_profit_anchor_blocks():
    return [
        *_line(1, 10, "Form 1040 2024 U.S. Individual Income Tax Return"),
        *_line(1, 30, "9 Total income 50,000"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 80, "31 Net profit or loss Line 31"),
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
