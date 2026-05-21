from uuid import uuid4

from app.models.document import Document
from app.repositories import document_repo


def make_document(case_id, broker_id=None):
    return Document(
        id=str(uuid4()),
        filename="bank.pdf",
        doc_type="bank_statement",
        storage_path="storage/path/bank.pdf",
        case_id=str(case_id),
        broker_id=str(broker_id) if broker_id else None,
    )


def test_list_documents_by_case_returns_all_case_documents(test_db):
    case_id = uuid4()
    first_document = make_document(case_id, uuid4())
    second_document = make_document(case_id, uuid4())
    test_db.add_all([first_document, second_document])
    test_db.commit()

    documents = document_repo.list_documents_by_case(test_db, case_id)

    assert {document.id for document in documents} == {
        first_document.id,
        second_document.id,
    }


def test_list_documents_by_case_filters_by_broker(test_db):
    case_id = uuid4()
    broker_id = uuid4()
    broker_document = make_document(case_id, broker_id)
    other_document = make_document(case_id, uuid4())
    test_db.add_all([broker_document, other_document])
    test_db.commit()

    documents = document_repo.list_documents_by_case(test_db, case_id, broker_id)

    assert [document.id for document in documents] == [broker_document.id]
