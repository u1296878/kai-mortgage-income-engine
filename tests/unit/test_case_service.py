from uuid import uuid4

import pytest

from app.exceptions import CaseNotFound
from app.models.case import Case
from app.models.document import Document
from app.services import case_service


def make_case(title="Johnson Refinance 2024"):
    return Case(id=str(uuid4()), title=title)


def make_document(case_id):
    return Document(
        id=str(uuid4()),
        filename="w2.pdf",
        doc_type="w2",
        storage_path="storage/path/w2.pdf",
        case_id=str(case_id),
    )


def test_create_case_saves_record(test_db):
    case = case_service.create_case(test_db, "Johnson Refinance 2024")

    assert case.title == "Johnson Refinance 2024"


def test_create_case_sets_status_to_open(test_db):
    case = case_service.create_case(test_db, "Johnson Refinance 2024")

    assert case.status == "open"


def test_get_case_with_documents_returns_linked_documents(test_db):
    case = make_case()
    document = make_document(case.id)
    test_db.add_all([case, document])
    test_db.commit()

    result = case_service.get_case_with_documents(test_db, case.id)

    assert str(result.id) == case.id
    assert [str(linked.id) for linked in result.documents] == [document.id]


def test_get_case_with_documents_returns_empty_list_when_no_documents(test_db):
    case = make_case()
    test_db.add(case)
    test_db.commit()

    result = case_service.get_case_with_documents(test_db, case.id)

    assert result.documents == []


def test_list_cases_returns_all_cases(test_db):
    first_case = make_case()
    second_case = make_case()
    test_db.add_all([first_case, second_case])
    test_db.commit()

    cases = case_service.list_cases(test_db)

    assert {case.id for case in cases} == {first_case.id, second_case.id}


def test_update_case_changes_title(test_db):
    case = make_case()
    test_db.add(case)
    test_db.commit()

    updated_case = case_service.update_case(test_db, case.id, {"title": "New Title"})

    assert updated_case.title == "New Title"


def test_update_case_changes_status(test_db):
    case = make_case()
    test_db.add(case)
    test_db.commit()

    updated_case = case_service.update_case(test_db, case.id, {"status": "in_review"})

    assert updated_case.status == "in_review"


def test_get_missing_case_raises(test_db):
    with pytest.raises(CaseNotFound):
        case_service.get_case_with_documents(test_db, uuid4())


def test_delete_missing_case_raises(test_db):
    with pytest.raises(CaseNotFound):
        case_service.delete_case(test_db, uuid4())
