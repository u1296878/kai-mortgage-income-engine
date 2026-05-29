from uuid import uuid4

import pytest

from app.exceptions import CaseNotFound
from app.models.case import Case
from app.models.document import Document
from app.models.user import User
from app.services import case_service


def make_case(title="Johnson Refinance 2024", broker_id=None):
    return Case(
        id=str(uuid4()),
        broker_id=str(broker_id or uuid4()),
        title=title,
    )


def make_document(case_id, broker_id=None):
    return Document(
        id=str(uuid4()),
        filename="w2.pdf",
        doc_type="w2",
        storage_path="storage/path/w2.pdf",
        case_id=str(case_id),
        broker_id=str(broker_id) if broker_id else None,
    )


def make_user(user_id=None, role="broker"):
    return User(
        id=str(user_id or uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="hash",
        role=role,
    )


def test_create_case_saves_record(test_db):
    broker_id = uuid4()
    manager = make_user(role="manager")

    case = case_service.create_case(
        test_db,
        "Johnson Refinance 2024",
        broker_id,
        manager,
    )

    assert case.title == "Johnson Refinance 2024"
    assert case.broker_id == str(broker_id)


def test_create_case_sets_status_to_open(test_db):
    broker_id = uuid4()
    manager = make_user(role="manager")

    case = case_service.create_case(
        test_db,
        "Johnson Refinance 2024",
        broker_id,
        manager,
    )

    assert case.status == "open"


def test_get_case_with_documents_returns_linked_documents(test_db):
    user = make_user()
    case = make_case()
    user.id = case.broker_id
    document = make_document(case.id, case.broker_id)
    test_db.add_all([case, document])
    test_db.commit()

    result = case_service.get_case_with_documents(test_db, case.id, user)

    assert str(result.id) == case.id
    assert [str(linked.id) for linked in result.documents] == [document.id]


def test_get_case_with_documents_returns_empty_list_when_no_documents(test_db):
    user = make_user()
    case = make_case()
    user.id = case.broker_id
    test_db.add(case)
    test_db.commit()

    result = case_service.get_case_with_documents(test_db, case.id, user)

    assert result.documents == []


def test_list_cases_returns_all_when_no_broker_id(test_db):
    manager = make_user(role="manager")
    first_case = make_case()
    second_case = make_case()
    test_db.add_all([first_case, second_case])
    test_db.commit()

    cases = case_service.list_cases(test_db, manager)

    assert {case.id for case in cases} == {first_case.id, second_case.id}


def test_list_cases_filters_by_broker_id(test_db):
    broker_id = uuid4()
    manager = make_user(role="manager")
    broker_case = make_case(broker_id=broker_id)
    other_case = make_case()
    test_db.add_all([broker_case, other_case])
    test_db.commit()

    cases = case_service.list_cases(test_db, manager, broker_id)

    assert [case.id for case in cases] == [broker_case.id]


def test_update_case_changes_title(test_db):
    user = make_user()
    case = make_case()
    user.id = case.broker_id
    test_db.add(case)
    test_db.commit()

    updated_case = case_service.update_case(
        test_db,
        case.id,
        {"title": "New Title"},
        user,
    )

    assert updated_case.title == "New Title"


def test_update_case_changes_status(test_db):
    user = make_user()
    case = make_case()
    user.id = case.broker_id
    test_db.add(case)
    test_db.commit()

    updated_case = case_service.update_case(
        test_db,
        case.id,
        {"status": "in_review"},
        user,
    )

    assert updated_case.status == "in_review"


def test_get_missing_case_raises(test_db):
    case_id = uuid4()
    user = make_user()

    with pytest.raises(CaseNotFound):
        case_service.get_case_with_documents(test_db, case_id, user)


def test_delete_missing_case_raises(test_db):
    case_id = uuid4()
    user = make_user()

    with pytest.raises(CaseNotFound):
        case_service.delete_case(test_db, case_id, user)
