from pathlib import Path
from uuid import UUID

from app.extractors.bank_statement_extractor import extract_bank_statement_fields
from app.extractors.paystub_extractor import extract_paystub_fields
from app.extractors.rental_extractor import extract_rental_fields
from app.extractors.tax_return_extractor import extract_tax_return_fields
from app.extractors.w2_extractor import extract_w2_fields
from app.exceptions import UnsupportedDocumentType
from app.models.document_type import DocumentType
from app.parsers.ocr_parser import parse_with_ocr
from app.parsers.pdf_parser import parse_pdf
from app.schemas.extraction import ExtractedField


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
    if valid_doc_type == DocumentType.pay_stub:
        blocks = parse_pdf(file_path)
        if not blocks:
            blocks = parse_with_ocr(file_path)
        return extract_paystub_fields(blocks, document_id)
    if valid_doc_type == DocumentType.tax_return:
        blocks = parse_pdf(file_path)
        if not blocks:
            blocks = parse_with_ocr(file_path)
        return extract_tax_return_fields(blocks, document_id)
    if valid_doc_type == DocumentType.bank_statement:
        blocks = parse_pdf(file_path)
        if not blocks:
            blocks = parse_with_ocr(file_path)
        return extract_bank_statement_fields(blocks, document_id)
    blocks = parse_pdf(file_path)
    if not blocks:
        blocks = parse_with_ocr(file_path)
    return extract_rental_fields(blocks, document_id)
