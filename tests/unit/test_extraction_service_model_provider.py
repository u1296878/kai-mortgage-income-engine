from pathlib import Path
from uuid import uuid4

from app.services import extraction_service


def tax_return_blocks():
    return [
        {"text": "11", "page": 1, "x1": 10, "y1": 20, "x2": 20, "y2": 30},
        {"text": "Adjusted", "page": 1, "x1": 30, "y1": 20, "x2": 80, "y2": 30},
        {"text": "gross", "page": 1, "x1": 90, "y1": 20, "x2": 120, "y2": 30},
        {"text": "income", "page": 1, "x1": 130, "y1": 20, "x2": 170, "y2": 30},
        {"text": "79000.00", "page": 1, "x1": 200, "y1": 20, "x2": 260, "y2": 30},
    ]


def test_extract_fields_anthropic_provider_routes_to_vision(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service.settings, "extraction_backend", "model")
    monkeypatch.setattr(extraction_service.settings, "extraction_provider", "anthropic")
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: tax_return_blocks())
    monkeypatch.setattr(extraction_service, "_model_backend", lambda: object())
    monkeypatch.setattr(extraction_service, "render_pdf_pages", lambda file_path, pages: [b"page"])
    monkeypatch.setattr(extraction_service, "page_dimensions", lambda file_path, pages: {1: (612, 792)})

    def fake_extract(images, blocks, doc_id, doc_type, backend, page_numbers, page_sizes):
        assert images == [b"page"]
        assert doc_id == document_id
        assert doc_type == "tax_return"
        assert backend is not None
        assert page_numbers == [1]
        assert page_sizes == {1: (612, 792)}
        return []

    monkeypatch.setattr(extraction_service, "extract_fields_with_vision", fake_extract)

    assert extraction_service.extract_fields(document_id, Path("tax.pdf"), "tax_return") == []
