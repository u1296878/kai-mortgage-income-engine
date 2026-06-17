from uuid import uuid4

from app.models.document import Document
from app.repositories import document_repo


def make_document(case_id):
    return Document(
        id=str(uuid4()),
        filename="bank.pdf",
        doc_type="bank_statement",
        storage_path="storage/path/bank.pdf",
        case_id=str(case_id),
    )


def test_list_documents_by_case_returns_all_case_documents(test_db):
    case_id = uuid4()
    first_document = make_document(case_id)
    second_document = make_document(case_id)
    test_db.add_all([first_document, second_document])
    test_db.commit()

    documents = document_repo.list_documents_by_case(test_db, case_id)

    assert {document.id for document in documents} == {
        first_document.id,
        second_document.id,
    }
