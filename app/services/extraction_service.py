from pathlib import Path
from uuid import UUID

from app.config import settings
from app.extractors.bank_statement_extractor import extract_bank_statement_fields
from app.extractors.block_utils import is_amount
from app.extractors.model_backend import OllamaBackend
from app.extractors.model_extractor import extract_fields_with_model
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

    blocks = _parse_document(file_path, valid_doc_type)
    if settings.extraction_backend == "model":
        return extract_fields_with_model(
            blocks,
            document_id,
            valid_doc_type.value,
            _model_backend(),
        )
    return _extract_with_rules(blocks, document_id, valid_doc_type)


def _parse_document(file_path: Path, doc_type: DocumentType) -> list[dict]:
    blocks = parse_pdf(file_path)
    if not blocks or _needs_model_w2_ocr(blocks, doc_type):
        blocks = parse_with_ocr(file_path)
    return blocks


def _needs_model_w2_ocr(blocks: list[dict], doc_type: DocumentType) -> bool:
    if settings.extraction_backend != "model" or doc_type != DocumentType.w2:
        return False
    text = " ".join(block["text"].lower() for block in blocks)
    has_w2_labels = "wages" in text and "federal income tax withheld" in text
    return not has_w2_labels or not any(is_amount(block["text"]) for block in blocks)


def _extract_with_rules(
    blocks: list[dict],
    document_id: UUID,
    doc_type: DocumentType,
) -> list[ExtractedField]:
    if doc_type == DocumentType.w2:
        return extract_w2_fields(blocks, document_id)
    if doc_type == DocumentType.pay_stub:
        return extract_paystub_fields(blocks, document_id)
    if doc_type == DocumentType.tax_return:
        return extract_tax_return_fields(blocks, document_id)
    if doc_type == DocumentType.bank_statement:
        return extract_bank_statement_fields(blocks, document_id)
    # other currently represents rental-income documents until a dedicated type exists.
    return extract_rental_fields(blocks, document_id)


def _model_backend() -> OllamaBackend:
    return OllamaBackend()
