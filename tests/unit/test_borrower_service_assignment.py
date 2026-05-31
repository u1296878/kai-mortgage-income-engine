from uuid import UUID, uuid4

import pytest

from app.exceptions import IncomeStreamNotFound, InvalidBorrowerAssignment
from app.models.borrower_role import BorrowerRole
from app.models.income_stream_type import IncomeStreamType
from app.services import borrower_service, income_stream_service
from tests.unit.income_stream_test_helpers import make_case, make_user


def test_assign_stream_to_borrower_requires_same_case(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case_a = make_case(broker_id)
    case_b = make_case(broker_id)
    test_db.add_all([case_a, case_b])
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case_a.id),
        "Case",
        "A",
        BorrowerRole.primary.value,
        broker,
    )
    stream = income_stream_service.create_income_stream(
        test_db,
        UUID(case_b.id),
        "Case B stream",
        IncomeStreamType.employment.value,
        None,
        broker,
    )

    with pytest.raises(InvalidBorrowerAssignment):
        borrower_service.assign_income_stream_to_borrower(
            test_db,
            UUID(borrower.id),
            UUID(stream.id),
            broker,
        )


def test_same_case_validation_blocks_cross_case_assignment_even_for_manager(test_db):
    broker_id = uuid4()
    manager = make_user(role="manager")
    broker = make_user(broker_id)
    case_a = make_case(broker_id)
    case_b = make_case(broker_id)
    test_db.add_all([case_a, case_b])
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case_a.id),
        "Manager",
        "Check",
        BorrowerRole.primary.value,
        manager,
    )
    stream = income_stream_service.create_income_stream(
        test_db,
        UUID(case_b.id),
        "Case B stream",
        IncomeStreamType.employment.value,
        None,
        broker,
    )

    with pytest.raises(InvalidBorrowerAssignment):
        borrower_service.assign_income_stream_to_borrower(
            test_db,
            UUID(borrower.id),
            UUID(stream.id),
            manager,
        )


def test_broker_cannot_assign_other_broker_stream(test_db):
    broker_id = uuid4()
    other_broker_id = uuid4()
    broker = make_user(broker_id)
    other_broker = make_user(other_broker_id)
    own_case = make_case(broker_id)
    other_case = make_case(other_broker_id)
    test_db.add_all([own_case, other_case])
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(own_case.id),
        "Own",
        "Borrower",
        BorrowerRole.primary.value,
        broker,
    )
    stream = income_stream_service.create_income_stream(
        test_db,
        UUID(other_case.id),
        "Other stream",
        IncomeStreamType.employment.value,
        None,
        other_broker,
    )

    with pytest.raises(IncomeStreamNotFound):
        borrower_service.assign_income_stream_to_borrower(
            test_db,
            UUID(borrower.id),
            UUID(stream.id),
            broker,
        )


def test_unassign_stream_from_borrower_preserves_stream(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    test_db.add(case)
    test_db.commit()
    borrower = borrower_service.create_borrower(
        test_db,
        UUID(case.id),
        "Clear",
        "Borrower",
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

    cleared = borrower_service.clear_income_stream_borrower(
        test_db,
        UUID(borrower.id),
        UUID(stream.id),
        broker,
    )

    assert cleared.id == stream.id
    assert cleared.borrower_id is None
