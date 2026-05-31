from uuid import UUID, uuid4

import pytest

from app.exceptions import BorrowerNotFound, CaseNotFound
from app.models.borrower_role import BorrowerRole
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
        BorrowerRole.primary.value,
        broker,
    )

    assert borrower.case_id == case.id
    assert borrower.broker_id == case.broker_id
    assert borrower.role == BorrowerRole.primary.value


def test_broker_cannot_create_borrower_for_other_broker_case(test_db):
    case = make_case(uuid4())
    broker = make_user()
    test_db.add(case)
    test_db.commit()

    with pytest.raises(CaseNotFound):
        borrower_service.create_borrower(
            test_db,
            UUID(case.id),
            "Bob",
            "Jones",
            BorrowerRole.primary.value,
            broker,
        )


def test_manager_can_create_borrower_for_any_case(test_db):
    case = make_case(uuid4())
    manager = make_user(role="manager")
    test_db.add(case)
    test_db.commit()

    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Jamie",
        "Lee",
        BorrowerRole.co_borrower.value,
        manager,
    )

    assert borrower.case_id == case.id


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
        BorrowerRole.primary.value,
        broker,
    )

    own = borrower_service.list_borrowers_by_case(test_db, UUID(own_case.id), broker)
    assert [borrower.first_name for borrower in own] == ["Own"]

    with pytest.raises(CaseNotFound):
        borrower_service.list_borrowers_by_case(test_db, UUID(other_case.id), broker)


def test_broker_cannot_get_other_broker_borrower(test_db):
    owner_id = uuid4()
    owner = make_user(owner_id)
    outsider = make_user()
    case = make_case(owner_id)
    test_db.add(case)
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Private",
        "Borrower",
        BorrowerRole.primary.value,
        owner,
    )

    with pytest.raises(BorrowerNotFound):
        borrower_service.get_borrower(test_db, UUID(borrower.id), outsider)


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
        BorrowerRole.primary.value,
        broker,
    )

    updated = borrower_service.update_borrower(
        test_db,
        UUID(borrower.id),
        {"first_name": "New", "role": BorrowerRole.co_borrower},
        broker,
    )

    assert updated.first_name == "New"
    assert updated.role == BorrowerRole.co_borrower.value


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
        BorrowerRole.primary.value,
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
