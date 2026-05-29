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


def paystub_blocks():
    return [
        {"text": "YTD Gross", "page": 1, "x1": 10, "y1": 20, "x2": 80, "y2": 30},
        {"text": "$42,500.00", "page": 1, "x1": 100, "y1": 20, "x2": 170, "y2": 30},
        {"text": "Gross Pay", "page": 1, "x1": 10, "y1": 50, "x2": 80, "y2": 60},
        {"text": "$3,269.23", "page": 1, "x1": 100, "y1": 50, "x2": 170, "y2": 60},
    ]


def tax_return_blocks():
    return [
        {"text": "11", "page": 1, "x1": 10, "y1": 20, "x2": 20, "y2": 30},
        {"text": "Adjusted", "page": 1, "x1": 30, "y1": 20, "x2": 80, "y2": 30},
        {"text": "gross", "page": 1, "x1": 90, "y1": 20, "x2": 120, "y2": 30},
        {"text": "income", "page": 1, "x1": 130, "y1": 20, "x2": 170, "y2": 30},
        {"text": "79000.00", "page": 1, "x1": 200, "y1": 20, "x2": 260, "y2": 30},
    ]


def bank_statement_blocks():
    return [
        {"text": "Statement Period:", "page": 1, "x1": 10, "y1": 10, "x2": 90, "y2": 20},
        {"text": "2024-01-01", "page": 1, "x1": 100, "y1": 10, "x2": 170, "y2": 20},
        {"text": "to", "page": 1, "x1": 180, "y1": 10, "x2": 190, "y2": 20},
        {"text": "2024-03-31", "page": 1, "x1": 200, "y1": 10, "x2": 270, "y2": 20},
        {"text": "Payroll Deposit", "page": 1, "x1": 10, "y1": 50, "x2": 100, "y2": 60},
        {"text": "5000.00", "page": 1, "x1": 200, "y1": 50, "x2": 250, "y2": 60},
    ]


def test_extract_fields_w2_returns_correct_fields(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: w2_blocks())

    fields = extraction_service.extract_fields(document_id, Path("w2.pdf"), "w2")

    assert [field.field for field in fields] == [
        "w2_wages",
        "w2_federal_tax_withheld",
    ]


def test_extract_fields_pay_stub_returns_correct_fields(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: paystub_blocks())

    fields = extraction_service.extract_fields(document_id, Path("pay.pdf"), "pay_stub")

    assert [field.field for field in fields] == ["gross_ytd", "gross_this_period"]


def test_extract_fields_tax_return_returns_real_fields(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: tax_return_blocks())

    fields = extraction_service.extract_fields(document_id, Path("tax.pdf"), "tax_return")

    assert [field.field for field in fields] == ["agi"]


def test_extract_fields_bank_statement_returns_real_fields(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(extraction_service, "parse_pdf", lambda file_path: bank_statement_blocks())

    fields = extraction_service.extract_fields(document_id, Path("bank.pdf"), "bank_statement")

    assert "average_monthly_deposit" in {field.field for field in fields}


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
    monkeypatch.setattr(
        extraction_service,
        "parse_pdf",
        lambda file_path: (
            paystub_blocks()
            if "pay" in str(file_path)
            else tax_return_blocks()
            if "tax_return" in str(file_path)
            else bank_statement_blocks()
            if "bank_statement" in str(file_path)
            else w2_blocks()
        ),
    )

    field_counts = [
        len(extraction_service.extract_fields(document_id, Path(f"{doc_type}.pdf"), doc_type))
        for doc_type in DocumentType
    ]

    assert all(count >= 1 for count in field_counts)
