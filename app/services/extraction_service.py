from pathlib import Path
from uuid import UUID

from app.extractors.w2_extractor import extract_w2_fields
from app.exceptions import UnsupportedDocumentType
from app.models.document_type import DocumentType
from app.parsers.ocr_parser import parse_with_ocr
from app.parsers.pdf_parser import parse_pdf
from app.schemas.extraction import BoundingBox, ExtractedField

STUB_FIELDS = {
    DocumentType.pay_stub: (
        ("gross_ytd", 42500.00),
        ("gross_per_period", 3269.23),
    ),
    DocumentType.tax_return: (
        ("agi", 79000.00),
        ("wages", 85000.00),
    ),
    DocumentType.bank_statement: (
        ("average_monthly_deposit", 7200.00),
        ("months_sampled", 3.0),
    ),
    DocumentType.other: (
        ("reported_income", 50000.00),
        ("period_months", 12.0),
    ),
}


def extract_fields(
    document_id: UUID,
    file_path: Path,
    doc_type: str,
) -> list[ExtractedField]:
    try:
        valid_doc_type = DocumentType(doc_type)
    except ValueError as error:
        raise UnsupportedDocumentType(f"Unsupported document type: {doc_type}") from error

    if valid_doc_type == DocumentType.w2:
        blocks = parse_pdf(file_path)
        if not blocks:
            blocks = parse_with_ocr(file_path)
        return extract_w2_fields(blocks, document_id)
    return _stub_fields(document_id, valid_doc_type)


def _stub_fields(document_id: UUID, doc_type: DocumentType) -> list[ExtractedField]:
    # STUB: non-W-2 document types keep mock data until their real parsers exist.
    # TODO: Replace with per-document extractors as Phase 2 expands.
    return [
        ExtractedField(
            field=field,
            value=value,
            document_id=document_id,
            page=1,
            bounding_box=BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
        )
        for field, value in STUB_FIELDS[doc_type]
    ]
