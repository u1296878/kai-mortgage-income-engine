from pathlib import Path
from uuid import uuid4

import pytest

from app.exceptions import UnsupportedDocumentType
from app.models.document_type import DocumentType
from app.services import extraction_service


def w2_blocks():
    return [
        {
            "text": "Wages, tips, other compensation",
            "page": 1,
            "x1": 10,
            "y1": 20,
            "x2": 80,
            "y2": 30,
        },
        {"text": "85000.00", "page": 1, "x1": 100, "y1": 20, "x2": 160, "y2": 30},
        {
            "text": "Federal income tax withheld",
            "page": 1,
            "x1": 10,
            "y1": 50,
            "x2": 90,
            "y2": 60,
        },
        {"text": "12000.00", "page": 1, "x1": 100, "y1": 50, "x2": 160, "y2": 60},
    ]


def test_extract_fields_w2_returns_correct_fields(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: w2_blocks())

    fields = extraction_service.extract_fields(document_id, Path("w2.pdf"), "w2")

    assert [field.field for field in fields] == [
        "w2_wages",
        "w2_federal_tax_withheld",
    ]


def test_extract_fields_pay_stub_returns_correct_fields():
    document_id = uuid4()

    fields = extraction_service.extract_fields(document_id, Path("pay.pdf"), "pay_stub")

    assert [field.field for field in fields] == ["gross_ytd", "gross_per_period"]


def test_extract_fields_returns_source_references(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: w2_blocks())

    fields = extraction_service.extract_fields(document_id, Path("w2.pdf"), "w2")

    assert all(field.document_id == document_id for field in fields)
    assert all(field.page == 1 for field in fields)
    assert all(field.bounding_box.x1 > 0.0 for field in fields)


def test_extract_fields_unsupported_type_raises():
    document_id = uuid4()

    with pytest.raises(UnsupportedDocumentType):
        extraction_service.extract_fields(document_id, Path("bad.pdf"), "passport")


def test_extract_fields_all_doc_types_return_fields(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: w2_blocks())

    field_counts = [
        len(extraction_service.extract_fields(document_id, Path("doc.pdf"), doc_type))
        for doc_type in DocumentType
    ]

    assert all(count >= 2 for count in field_counts)
