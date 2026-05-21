from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import UploadFile

from app.exceptions import DocumentNotFound, UnsupportedDocumentType
from app.models.document import Document
from app.services import document_service


def make_upload_file(filename: str = "paystub.pdf") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(b"file contents"))


def test_upload_document_saves_file(test_db, tmp_path, monkeypatch):
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    file = make_upload_file()

    document = document_service.upload_document(test_db, file, "pay_stub")

    assert (tmp_path / document.id / "paystub.pdf").exists()


def test_upload_document_saves_record(test_db, tmp_path, monkeypatch):
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    file = make_upload_file("w2.pdf")

    document = document_service.upload_document(test_db, file, "w2")

    assert document.id is not None
    assert document.filename == "w2.pdf"
    assert document.doc_type == "w2"
    assert document.case_id is None


def test_upload_invalid_doc_type_raises(test_db, tmp_path, monkeypatch):
    monkeypatch.setattr(document_service.settings, "storage_path", str(tmp_path))
    file = make_upload_file()

    with pytest.raises(UnsupportedDocumentType):
        document_service.upload_document(test_db, file, "passport")


def test_link_document_to_case(test_db):
    document = Document(
        id=str(uuid4()),
        filename="tax.pdf",
        doc_type="tax_return",
        storage_path="storage/path/tax.pdf",
    )
    test_db.add(document)
    test_db.commit()
    case_id = uuid4()

    linked_document = document_service.link_document_to_case(
        test_db,
        document.id,
        case_id,
    )

    assert linked_document.case_id == str(case_id)


def test_link_missing_document_raises(test_db):
    document_id = uuid4()
    case_id = uuid4()

    with pytest.raises(DocumentNotFound):
        document_service.link_document_to_case(test_db, document_id, case_id)
