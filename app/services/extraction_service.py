from pathlib import Path
from uuid import UUID

from app.exceptions import UnsupportedDocumentType
from app.models.document_type import DocumentType
from app.schemas.extraction import BoundingBox, ExtractedField

# STUB: returns hardcoded extraction fields until parser/extractor layers exist.
# TODO: Replace with real parsers and extractors (see app/parsers/ and app/extractors/)

STUB_FIELDS = {
    DocumentType.w2: (
        ("w2_wages", 85000.00),
        ("w2_federal_tax_withheld", 12000.00),
    ),
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
    _file_path: Path,
    doc_type: str,
) -> list[ExtractedField]:
    try:
        valid_doc_type = DocumentType(doc_type)
    except ValueError as error:
        raise UnsupportedDocumentType(f"Unsupported document type: {doc_type}") from error

    return [
        ExtractedField(
            field=field,
            value=value,
            document_id=document_id,
            page=1,
            bounding_box=BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
        )
        for field, value in STUB_FIELDS[valid_doc_type]
    ]
