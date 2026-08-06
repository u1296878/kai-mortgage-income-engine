from pathlib import Path
from uuid import uuid4

from app.services import extraction_service
from app.extractors.model_extractor import extract_fields_with_model


class FakeBackend:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.prompts = []

    def complete_json(self, prompt: str, schema: dict) -> dict:
        self.prompts.append(prompt)
        return self.payload


def test_model_w2_extractor_returns_fields_with_source_refs():
    document_id = uuid4()
    backend = FakeBackend(
        {
            "fields": {
                "tax_year": {"value": 2024, "confidence": 0.9, "source_text": "2024", "source_line_ids": ["L0001"]},
                "w2_wages": {"value": 85000, "confidence": 0.92, "source_text": "85,000.00", "source_line_ids": ["L0001"]},
                "w2_employer_name": {"value": None, "confidence": 0.8, "source_text": "Acme LLC", "source_line_ids": ["L0001"]},
            }
        }
    )

    fields = extract_fields_with_model(_w2_blocks(), document_id, "w2", backend)
    by_name = {field.field: field for field in fields}

    assert by_name["w2_wages"].value == 85000
    assert by_name["w2_wages"].page == 1
    assert by_name["w2_wages"].bounding_box.x1 == 20
    assert by_name["w2_employer_name"].raw_text == "Employer name Acme LLC"
    assert any("w2_wages" in prompt for prompt in backend.prompts)


def test_model_w2_extractor_corrects_box_label_value():
    document_id = uuid4()
    backend = FakeBackend(
        {"fields": {"w2_wages": {"value": 1, "confidence": 0.9, "source_text": "1", "source_line_ids": ["L0001"]}}}
    )

    fields = extract_fields_with_model(_w2_blocks(), document_id, "w2", backend)
    wages = next(field for field in fields if field.field == "w2_wages")

    assert wages.value == 85000
    assert wages.raw_text == "1 Wages tips other compensation 85,000.00"


def test_model_w2_extractor_recovers_missing_wages_from_box_anchor():
    document_id = uuid4()
    backend = FakeBackend(
        {"fields": {"w2_wages": {"value": None, "confidence": 0.2, "source_text": None}}}
    )

    fields = extract_fields_with_model(_w2_blocks(), document_id, "w2", backend)
    wages = next(field for field in fields if field.field == "w2_wages")

    assert wages.value == 85000
    assert wages.confidence == 0.6


def test_model_w2_extractor_recovers_missing_tax_year_from_w2_context():
    document_id = uuid4()
    backend = FakeBackend(
        {"fields": {"tax_year": {"value": None, "confidence": 0.2, "source_text": None}}}
    )

    fields = extract_fields_with_model(_w2_blocks(), document_id, "w2", backend)
    tax_year = next(field for field in fields if field.field == "tax_year")

    assert tax_year.value == 2024
    assert tax_year.page == 1


def test_extraction_service_model_backend_routes_w2_to_model(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service.settings, "extraction_backend", "model")
    monkeypatch.setattr(extraction_service.settings, "extraction_provider", "ollama")
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: _w2_blocks())
    monkeypatch.setattr(extraction_service, "_model_backend", lambda: object())

    def fake_extract(blocks, doc_id, doc_type, backend):
        assert doc_id == document_id
        assert doc_type == "w2"
        assert len(blocks) == len(_w2_blocks())
        return []

    monkeypatch.setattr(extraction_service, "extract_fields_with_model", fake_extract)

    assert extraction_service.extract_fields(document_id, Path("w2.pdf"), "w2") == []


def _w2_blocks() -> list[dict]:
    return [
        *_line(1, 10, "2024 Form W-2 Wage and Tax Statement"),
        *_line(1, 30, "Employer name Acme LLC"),
        *_line(1, 50, "Employee name Jane Worker"),
        *_line(1, 80, "1 Wages tips other compensation 85,000.00"),
        *_line(1, 100, "2 Federal income tax withheld 12,500.00"),
        *_line(1, 120, "3 Social security wages 85,000.00"),
        *_line(1, 140, "5 Medicare wages and tips 85,000.00"),
    ]


def _line(page: int, y: float, text: str) -> list[dict]:
    blocks = []
    x = 20
    for word in text.split():
        width = max(10, len(word) * 5)
        blocks.append({"text": word, "page": page, "x1": x, "y1": y, "x2": x + width, "y2": y + 10})
        x += width + 10
    return blocks
