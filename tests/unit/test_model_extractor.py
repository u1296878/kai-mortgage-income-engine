from uuid import uuid4

from app.extractors.model_extractor import extract_fields_with_model
from app.services import extraction_validation


class FakeBackend:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.prompts = []
        self.schemas = []

    def complete_json(self, prompt: str, schema: dict) -> dict:
        self.prompts.append(prompt)
        self.schemas.append(schema)
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
    assert by_name["schedule_c_net_profit"].bounding_box.x1 == 230
    assert by_name["schedule_c_net_profit"].raw_text == "94,380"
    assert by_name["schedule_c_net_profit"].confidence == 0.91
    assert any("schedule_c_net_profit" in prompt for prompt in backend.prompts)
    assert "unrelated page" not in "\n".join(backend.prompts)
    assert "fields" in backend.schemas[0]["properties"]


def test_model_extractor_flags_null_without_fabricated_source():
    document_id = uuid4()
    backend = FakeBackend(
        {"fields": {"schedule_c_meals_exclusion": {"value": None, "confidence": 0.4, "source_text": None}}}
    )

    fields = extract_fields_with_model(_blocks(), document_id, "tax_return", backend)

    field = next(field for field in fields if field.field == "schedule_c_meals_exclusion")
    assert field.value is None
    assert field.page is None
    assert field.bounding_box is None
    assert field.confidence == 0.0


def test_model_extractor_corrects_blank_line_number_value():
    document_id = uuid4()
    backend = FakeBackend(
        {"fields": {"schedule_c_depletion": {"value": 12, "confidence": 0.9, "source_text": "12 Depletion 12"}}}
    )

    fields = extract_fields_with_model(_blocks(), document_id, "tax_return", backend)

    depletion = next(field for field in fields if field.field == "schedule_c_depletion")
    assert depletion.value is None
    assert depletion.bounding_box is None
    assert depletion.confidence == 0.2


def test_model_extractor_recovers_visible_amount_when_model_returns_line_label():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "schedule_c_business_use_of_home": {
                    "value": 30,
                    "confidence": 0.9,
                    "source_text": "line 30",
                }
            }
        }
    )

    fields = extract_fields_with_model(_blocks(), document_id, "tax_return", backend)

    home = next(field for field in fields if field.field == "schedule_c_business_use_of_home")
    assert home.value == 4628
    assert home.page == 8
    assert home.confidence == 0.9


def test_model_extractor_does_not_recover_amount_from_next_line():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "schedule_c_business_use_of_home": {
                    "value": 30,
                    "confidence": 0.9,
                    "source_text": "line 30",
                }
            }
        }
    )

    fields = extract_fields_with_model(_blank_home_blocks(), document_id, "tax_return", backend)

    home = next(field for field in fields if field.field == "schedule_c_business_use_of_home")
    assert home.value is None
    assert home.page is None
    assert home.bounding_box is None
    assert home.confidence == 0.2


def test_model_extractor_reconciles_net_profit_against_form_line():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "schedule_c_net_profit": {
                    "value": 1,
                    "confidence": 0.95,
                    "source_text": "Line 31 1",
                }
            }
        }
    )

    fields = extract_fields_with_model(_mismatched_net_profit_blocks(), document_id, "tax_return", backend)

    net_profit = next(field for field in fields if field.field == "schedule_c_net_profit")
    issues = extraction_validation.validate_extraction("tax_return", fields)
    high_issue = next(issue for issue in issues if issue["severity"] == "high")
    assert net_profit.value == 85247
    assert net_profit.raw_text == "85,247"
    assert extraction_validation.has_high_issue(issues)
    assert high_issue == {
        "fields": ["schedule_c_net_profit"],
        "message": "schedule_c_net_profit: model read 1 but Form line 31 shows 85,247; used the form value; verify.",
        "severity": "high",
    }


def test_model_extractor_keeps_agreeing_anchor_clean():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "schedule_c_net_profit": {
                    "value": 94380,
                    "confidence": 0.95,
                    "source_text": "Line 31 94,380",
                }
            }
        }
    )

    fields = extract_fields_with_model(_blocks(), document_id, "tax_return", backend)

    net_profit = next(field for field in fields if field.field == "schedule_c_net_profit")
    issues = extraction_validation.validate_extraction("tax_return", fields)
    assert net_profit.value == 94380
    assert not any("model read" in issue["message"] for issue in issues)


def test_model_extractor_keeps_model_value_when_anchor_missing():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "schedule_c_net_profit": {
                    "value": 50000,
                    "confidence": 0.95,
                    "source_text": None,
                }
            }
        }
    )

    fields = extract_fields_with_model(_missing_net_profit_anchor_blocks(), document_id, "tax_return", backend)

    net_profit = next(field for field in fields if field.field == "schedule_c_net_profit")
    issues = extraction_validation.validate_extraction("tax_return", fields)
    assert net_profit.value == 50000
    assert not any("model read" in issue["message"] for issue in issues)


def _blocks():
    return [
        *_line(1, 10, "Form 1040 2023 U.S. Individual Income Tax Return"),
        *_line(1, 30, "9 Total income 94,380"),
        *_line(1, 50, "11 Adjusted gross income 87,638"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 30, "12 Depletion 12"),
        *_line(8, 40, "13 Depreciation and section 179 13 3,633"),
        *_line(8, 60, "30 business use of home line 30 4,628"),
        *_line(8, 80, "31 Net profit or loss Line 31 94,380"),
        *_line(99, 10, "unrelated page 12345"),
    ]


def _line(page: int, y: float, text: str) -> list[dict]:
    blocks = []
    x = 20
    for word in text.split():
        blocks.append({"text": word, "page": page, "x1": x, "y1": y, "x2": x + 10, "y2": y + 10})
        x += 30
    return blocks


def _blank_home_blocks():
    return [
        *_line(1, 10, "Form 1040 2023 U.S. Individual Income Tax Return"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 60, "30 business use of home line 30"),
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
