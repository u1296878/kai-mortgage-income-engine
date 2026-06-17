from uuid import UUID, uuid4

import pytest

from app.exceptions import BorrowerNotFound
from app.models.income_stream_type import IncomeStreamType
from app.services import borrower_service, income_stream_service
from tests.unit.income_stream_test_helpers import make_case, make_user


def test_create_borrower_sets_case(test_db):
    user = make_user()
    case = make_case()
    test_db.add(case)
    test_db.commit()

    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Alice",
        "Smith",
        "primary",
    )

    assert borrower.case_id == case.id
    assert borrower.role == "primary"


def test_list_borrowers_returns_case_borrowers(test_db):
    user = make_user()
    own_case = make_case()
    other_case = make_case(uuid4())
    test_db.add_all([own_case, other_case])
    test_db.commit()
    borrower_service.create_borrower(
        test_db,
        UUID(own_case.id),
        "Own",
        "Borrower",
        "primary",
    )

    own = borrower_service.list_borrowers_by_case(test_db, UUID(own_case.id))
    assert [borrower.first_name for borrower in own] == ["Own"]

    other = borrower_service.list_borrowers_by_case(test_db, UUID(other_case.id))
    assert other == []


def test_update_borrower_changes_metadata(test_db):
    user = make_user()
    case = make_case()
    test_db.add(case)
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Old",
        "Name",
        "primary",
    )

    updated = borrower_service.update_borrower(
        test_db,
        UUID(borrower.id),
        {"first_name": "New", "role": "co_borrower"},
    )

    assert updated.first_name == "New"
    assert updated.role == "co_borrower"


def test_delete_borrower_clears_stream_assignments(test_db):
    user = make_user()
    case = make_case()
    test_db.add(case)
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Delete",
        "Me",
        "primary",
    )
    stream = income_stream_service.create_income_stream(
        test_db,
        UUID(case.id),
        "Employment",
        IncomeStreamType.employment.value,
        None,
    )
    borrower_service.assign_income_stream_to_borrower(
        test_db,
        UUID(borrower.id),
        UUID(stream.id),
    )

    borrower_service.delete_borrower(test_db, UUID(borrower.id))

    refreshed = income_stream_service.get_income_stream(test_db, UUID(stream.id))
    assert refreshed.borrower_id is None
