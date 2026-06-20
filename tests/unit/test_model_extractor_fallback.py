from uuid import uuid4

from app.extractors import model_value_guard
from app.extractors.model_extractor import extract_fields_with_model
from tests.unit.test_model_extractor import FakeBackend, _blocks


def test_model_extractor_recovers_net_profit_when_model_returns_label_text():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "schedule_c_net_profit": {
                    "value": "31 Net profit or loss. Subtract line 30 from line 29.",
                    "confidence": 0.9,
                    "source_text": "31 Net profit or loss",
                }
            }
        }
    )

    fields = extract_fields_with_model(_blocks(), document_id, "tax_return", backend)

    net_profit = next(field for field in fields if field.field == "schedule_c_net_profit")
    assert net_profit.value == 94380
    assert net_profit.page == 8
    assert net_profit.raw_text == "94,380"


def test_model_extractor_recovers_agi_when_model_omits_it():
    document_id = uuid4()
    backend = FakeBackend({"fields": {}})

    fields = extract_fields_with_model(_blocks(), document_id, "tax_return", backend)

    agi = next(field for field in fields if field.field == "agi")
    assert agi.value == 87638
    assert agi.page == 1


def test_model_value_guard_has_no_page_wide_money_fallback():
    assert not hasattr(model_value_guard, "_last_money_value")
