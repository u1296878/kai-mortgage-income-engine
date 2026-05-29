from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.exceptions import InvalidIncomeStreamAssignment, ResultNotFound
from app.models.income_stream_type import IncomeStreamType
from app.models.result import Result
from app.services import income_stream_service
from tests.unit.income_stream_test_helpers import make_case, make_result, make_user


def test_assign_result_to_stream_recalculates_income(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    older = make_result(
        case.id,
        85000.0,
        confidence="medium",
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    newer = make_result(
        case.id,
        87000.0,
        confidence="high",
        created_at=datetime.now(timezone.utc),
    )
    test_db.add_all([case, older, newer])
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case.id,
        "Employment",
        IncomeStreamType.employment.value,
        None,
        broker,
    )
    income_stream_service.assign_result_to_stream(test_db, stream.id, older.id, broker)

    updated = income_stream_service.assign_result_to_stream(test_db, stream.id, newer.id, broker)

    assert updated.annual_income == 87000.0
    assert updated.confidence == "high"


def test_assign_result_to_stream_rejects_different_case_for_broker_and_manager(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    manager = make_user(role="manager")
    case_a = make_case(broker_id)
    case_b = make_case(broker_id)
    result = make_result(case_b.id, 85000.0)
    test_db.add_all([case_a, case_b, result])
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case_a.id,
        "Case A stream",
        IncomeStreamType.employment.value,
        None,
        broker,
    )

    with pytest.raises(InvalidIncomeStreamAssignment):
        income_stream_service.assign_result_to_stream(test_db, stream.id, result.id, broker)
    with pytest.raises(InvalidIncomeStreamAssignment):
        income_stream_service.assign_result_to_stream(test_db, stream.id, result.id, manager)
    unchanged_result = test_db.get(Result, result.id)
    unchanged_stream = income_stream_service.get_income_stream(test_db, stream.id, manager)
    assert unchanged_result.income_stream_id is None
    assert unchanged_stream.annual_income is None


def test_broker_cannot_assign_other_broker_result(test_db):
    owner_id = uuid4()
    other_id = uuid4()
    owner = make_user(owner_id)
    case_owner = make_case(owner_id)
    case_other = make_case(other_id)
    result = make_result(case_other.id, 92000.0)
    test_db.add_all([case_owner, case_other, result])
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case_owner.id,
        "Owner stream",
        IncomeStreamType.employment.value,
        None,
        owner,
    )

    with pytest.raises(ResultNotFound):
        income_stream_service.assign_result_to_stream(test_db, stream.id, result.id, owner)


def test_unassign_result_recalculates_income(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    low = make_result(case.id, 70000.0, confidence="low")
    high = make_result(case.id, 90000.0, confidence="high")
    test_db.add_all([case, low, high])
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case.id,
        "Income stream",
        IncomeStreamType.employment.value,
        None,
        broker,
    )
    income_stream_service.assign_result_to_stream(test_db, stream.id, low.id, broker)
    income_stream_service.assign_result_to_stream(test_db, stream.id, high.id, broker)

    updated = income_stream_service.unassign_result_from_stream(test_db, stream.id, high.id, broker)

    assert updated.annual_income == 70000.0
    assert updated.confidence == "low"
