from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import UploadFile

from app.exceptions import DocumentNotFound, UnsupportedDocumentType
from app.models.case import Case
from app.models.document import Document
from app.models.user import User
from app.services import document_service
from app.storage import local_storage


def make_upload_file(filename: str = "paystub.pdf") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(b"file contents"))


def make_user(user_id=None, role="broker"):
    return User(
        id=str(user_id or uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="hash",
        role=role,
    )


def test_upload_document_saves_file(test_db, tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    file = make_upload_file()
    user = make_user()

    document = document_service.upload_document(test_db, file, "pay_stub", user)

    assert (tmp_path / document.id / "document").exists()


def test_upload_document_saves_record(test_db, tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    file = make_upload_file("w2.pdf")
    user = make_user()

    document = document_service.upload_document(test_db, file, "w2", user)

    assert document.id is not None
    assert document.filename == "w2.pdf"
    assert document.doc_type == "w2"
    assert document.case_id is None


def test_upload_invalid_doc_type_raises(test_db, tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    file = make_upload_file()
    user = make_user()

    with pytest.raises(UnsupportedDocumentType):
        document_service.upload_document(test_db, file, "passport", user)


def test_link_document_to_case(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = Case(id=str(uuid4()), broker_id=str(broker_id), title="Smith Purchase")
    document = Document(
        id=str(uuid4()),
        filename="tax.pdf",
        doc_type="tax_return",
        storage_path="storage/path/tax.pdf",
        broker_id=str(broker_id),
    )
    test_db.add_all([case, document])
    test_db.commit()

    linked_document = document_service.link_document_to_case(
        test_db,
        document.id,
        case.id,
        user,
    )

    assert linked_document.case_id == case.id


def test_link_document_to_case_sets_broker_id(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = Case(id=str(uuid4()), broker_id=str(broker_id), title="Smith Purchase")
    document = Document(
        id=str(uuid4()),
        filename="tax.pdf",
        doc_type="tax_return",
        storage_path="storage/path/tax.pdf",
        broker_id=str(broker_id),
    )
    test_db.add_all([case, document])
    test_db.commit()

    linked_document = document_service.link_document_to_case(
        test_db,
        document.id,
        case.id,
        user,
    )

    assert linked_document.broker_id == str(broker_id)


def test_link_missing_document_raises(test_db):
    document_id = uuid4()
    case_id = uuid4()
    user = make_user()

    with pytest.raises(DocumentNotFound):
        document_service.link_document_to_case(test_db, document_id, case_id, user)


def test_link_missing_case_preserves_existing_behavior(test_db):
    manager = make_user(role="manager")
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
        manager,
    )

    assert linked_document.case_id == str(case_id)
    assert linked_document.broker_id is None
