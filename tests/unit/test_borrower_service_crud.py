from uuid import UUID, uuid4

import pytest

from app.exceptions import BorrowerNotFound, CaseNotFound
from app.models.income_stream_type import IncomeStreamType
from app.services import borrower_service, income_stream_service
from tests.unit.income_stream_test_helpers import make_case, make_user


def test_create_borrower_sets_case_and_broker(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    test_db.add(case)
    test_db.commit()

    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Alice",
        "Smith",
        "primary",
        broker,
    )

    assert borrower.case_id == case.id
    assert borrower.broker_id == case.broker_id
    assert borrower.role == "primary"


def test_list_borrowers_broker_sees_only_own_case_borrowers(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    own_case = make_case(broker_id)
    other_case = make_case(uuid4())
    test_db.add_all([own_case, other_case])
    test_db.commit()
    borrower_service.create_borrower(
        test_db,
        UUID(own_case.id),
        "Own",
        "Borrower",
        "primary",
        broker,
    )

    own = borrower_service.list_borrowers_by_case(test_db, UUID(own_case.id), broker)
    assert [borrower.first_name for borrower in own] == ["Own"]

    with pytest.raises(CaseNotFound):
        borrower_service.list_borrowers_by_case(test_db, UUID(other_case.id), broker)


def test_update_borrower_changes_metadata(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    test_db.add(case)
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Old",
        "Name",
        "primary",
        broker,
    )

    updated = borrower_service.update_borrower(
        test_db,
        UUID(borrower.id),
        {"first_name": "New", "role": "co_borrower"},
        broker,
    )

    assert updated.first_name == "New"
    assert updated.role == "co_borrower"


def test_delete_borrower_clears_stream_assignments(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    test_db.add(case)
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Delete",
        "Me",
        "primary",
        broker,
    )
    stream = income_stream_service.create_income_stream(
        test_db,
        UUID(case.id),
        "Employment",
        IncomeStreamType.employment.value,
        None,
        broker,
    )
    borrower_service.assign_income_stream_to_borrower(
        test_db,
        UUID(borrower.id),
        UUID(stream.id),
        broker,
    )

    borrower_service.delete_borrower(test_db, UUID(borrower.id), broker)

    refreshed = income_stream_service.get_income_stream(test_db, UUID(stream.id), broker)
    assert refreshed.borrower_id is None
