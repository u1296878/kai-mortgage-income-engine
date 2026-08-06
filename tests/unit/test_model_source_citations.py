from uuid import uuid4

from app.extractors.model_extractor import extract_fields_with_model


class FakeBackend:
    def __init__(self, fields: dict) -> None:
        self.payload = {"fields": fields}

    def complete_json(self, prompt: str, schema: dict) -> dict:
        return self.payload


def test_valid_citation_avoids_fuzzy_locator():
    fields = extract_fields_with_model(
        _duplicate_value_blocks(),
        uuid4(),
        "tax_return",
        FakeBackend({"schedule_c_net_profit": _entry(94380, "duplicate 94,380", ["L0002"])}),
    )

    net_profit = _field(fields, "schedule_c_net_profit")
    assert net_profit.value == 94380
    assert net_profit.bounding_box.y1 == 100
    assert net_profit.raw_text == "duplicate 94,380"


def test_missing_source_line_ids_downgrades_and_flags_with_fallback():
    fields = extract_fields_with_model(
        _tax_return_blocks(),
        uuid4(),
        "tax_return",
        FakeBackend({"schedule_c_net_profit": _entry(94380, "Line 31 94,380", None)}),
    )

    net_profit = _field(fields, "schedule_c_net_profit")
    assert net_profit.page == 8
    assert net_profit.confidence == 0.2
    assert _messages(net_profit) == [
        "source_line_ids missing for model value",
        "source located by fallback; verify",
    ]


def test_invalid_source_line_ids_downgrade_without_fallback_source():
    fields = extract_fields_with_model(
        _tax_return_blocks(),
        uuid4(),
        "tax_return",
        FakeBackend({"schedule_c_net_profit": _entry(94380, "Line 31 94,380", ["L9999"])}),
    )

    net_profit = _field(fields, "schedule_c_net_profit")
    assert net_profit.page is None
    assert net_profit.confidence == 0.2
    assert _messages(net_profit) == ["source_line_ids invalid: L9999"]


def test_cross_page_source_line_ids_downgrade_and_flag():
    fields = extract_fields_with_model(
        _cross_page_paystub_blocks(),
        uuid4(),
        "pay_stub",
        FakeBackend({"paystub_gross_ytd": _entry(45000, "45,000.00", ["L0001", "L0002"])}),
    )

    gross_ytd = _field(fields, "paystub_gross_ytd")
    assert gross_ytd.page is None
    assert gross_ytd.confidence == 0.2
    assert _messages(gross_ytd) == ["source_line_ids cross pages: L0001, L0002"]


def test_source_text_not_found_in_cited_source_downgrades_and_flags():
    fields = extract_fields_with_model(
        _paystub_blocks(),
        uuid4(),
        "pay_stub",
        FakeBackend({"paystub_gross_ytd": _entry(45000, "wrong text", ["L0001"])}),
    )

    gross_ytd = _field(fields, "paystub_gross_ytd")
    assert gross_ytd.page == 1
    assert gross_ytd.confidence == 0.2
    assert _messages(gross_ytd) == ["source_text not found in cited source"]


def test_value_not_found_in_cited_source_downgrades_and_flags():
    fields = extract_fields_with_model(
        _paystub_blocks(),
        uuid4(),
        "pay_stub",
        FakeBackend({"paystub_gross_ytd": _entry(1000, "YTD Gross 45,000.00", ["L0001"])}),
    )

    gross_ytd = _field(fields, "paystub_gross_ytd")
    assert gross_ytd.page == 1
    assert gross_ytd.confidence == 0.2
    assert _messages(gross_ytd) == ["value not found in cited source"]


def test_same_response_produces_identical_fields():
    document_id = uuid4()
    fields = {"paystub_gross_ytd": _entry(45000, "45,000.00", ["L0001"])}

    first = extract_fields_with_model(_paystub_blocks(), document_id, "pay_stub", FakeBackend(fields))
    second = extract_fields_with_model(_paystub_blocks(), document_id, "pay_stub", FakeBackend(fields))

    assert [field.model_dump(mode="json") for field in first] == [field.model_dump(mode="json") for field in second]


def _entry(value: float, source_text: str | None, source_line_ids: list[str] | None) -> dict:
    entry = {"value": value, "confidence": 0.95, "source_text": source_text}
    if source_line_ids is not None:
        entry["source_line_ids"] = source_line_ids
    return entry


def _tax_return_blocks():
    return [
        *_line(1, 10, "Form 1040 2023 U.S. Individual Income Tax Return"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 80, "31 Net profit or loss Line 31 94,380"),
    ]


def _duplicate_value_blocks():
    return [
        *_line(1, 10, "Form 1040 2023 U.S. Individual Income Tax Return"),
        *_line(8, 10, "SCHEDULE C Profit or Loss From Business"),
        *_line(8, 80, "31 Net profit or loss Line 31 94,380"),
        *_line(8, 100, "duplicate 94,380"),
    ]


def _paystub_blocks():
    return [*_line(1, 50, "YTD Gross 45,000.00"), *_line(1, 70, "Current Gross 3,750.00")]


def _cross_page_paystub_blocks():
    return [*_line(1, 50, "YTD Gross 45,000.00"), *_line(2, 70, "Current Gross 3,750.00")]


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
    return [issue["message"] for issue in field.review_flags]
