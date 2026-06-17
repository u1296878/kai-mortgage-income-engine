from uuid import UUID, uuid4

import pytest

from app.exceptions import IncomeStreamNotFound, InvalidBorrowerAssignment
from app.models.income_stream_type import IncomeStreamType
from app.services import borrower_service, income_stream_service
from tests.unit.income_stream_test_helpers import make_case, make_user


def test_assign_stream_to_borrower_requires_same_case(test_db):
    user = make_user()
    case_a = make_case()
    case_b = make_case()
    test_db.add_all([case_a, case_b])
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case_a.id),
        "Case",
        "A",
        "primary",
    )
    stream = income_stream_service.create_income_stream(
        test_db,
        UUID(case_b.id),
        "Case B stream",
        IncomeStreamType.employment.value,
        None,
    )

    with pytest.raises(InvalidBorrowerAssignment):
        borrower_service.assign_income_stream_to_borrower(
            test_db,
            UUID(borrower.id),
            UUID(stream.id),
        )


def test_same_case_validation_blocks_cross_case_assignment(test_db):
    user = make_user()
    case_a = make_case()
    case_b = make_case()
    test_db.add_all([case_a, case_b])
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case_a.id),
            "Manager",
            "Check",
            "primary",
    )
    stream = income_stream_service.create_income_stream(
        test_db,
        UUID(case_b.id),
        "Case B stream",
        IncomeStreamType.employment.value,
        None,
    )

    with pytest.raises(InvalidBorrowerAssignment):
        borrower_service.assign_income_stream_to_borrower(
            test_db,
            UUID(borrower.id),
            UUID(stream.id),
        )


def test_unassign_stream_from_borrower_preserves_stream(test_db):
    user = make_user()
    case = make_case()
    test_db.add(case)
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Clear",
        "Borrower",
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

    cleared = borrower_service.clear_income_stream_borrower(
        test_db,
        UUID(borrower.id),
        UUID(stream.id),
    )

    assert cleared.id == stream.id
    assert cleared.borrower_id is None
