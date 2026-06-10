from uuid import uuid4

import pytest

from app.exceptions import CaseNotFound, IncomeStreamNotFound
from app.models.income_stream_type import IncomeStreamType
from app.services import income_stream_service
from tests.unit.income_stream_test_helpers import make_case, make_result, make_user


def test_create_income_stream_sets_case_and_broker(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    test_db.add(case)
    test_db.commit()

    stream = income_stream_service.create_income_stream(
        test_db,
        case.id,
        "Primary job",
        IncomeStreamType.employment.value,
        "Main employer",
        broker,
    )

    assert stream.case_id == case.id
    assert stream.broker_id == case.broker_id
    assert stream.name == "Primary job"


def test_list_income_streams_broker_sees_only_own_case_streams(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    own_case = make_case(broker_id)
    other_case = make_case(uuid4())
    test_db.add_all([own_case, other_case])
    test_db.commit()
    income_stream_service.create_income_stream(
        test_db,
        own_case.id,
        "Own stream",
        IncomeStreamType.employment.value,
        None,
        broker,
    )

    with pytest.raises(CaseNotFound):
        income_stream_service.list_income_streams_by_case(test_db, other_case.id, broker)


def test_update_income_stream_changes_metadata(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    test_db.add(case)
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case.id,
        "Old",
        IncomeStreamType.other.value,
        None,
        broker,
    )

    updated = income_stream_service.update_income_stream(
        test_db,
        stream.id,
        {"name": "Updated", "stream_type": IncomeStreamType.rental},
        broker,
    )

    assert updated.name == "Updated"
    assert updated.stream_type == IncomeStreamType.rental.value


def test_delete_income_stream_clears_result_assignments(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = make_case(broker_id)
    result = make_result(case.id, 85000.0)
    test_db.add_all([case, result])
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case.id,
        "To delete",
        IncomeStreamType.employment.value,
        None,
        broker,
    )
    income_stream_service.assign_result_to_stream(test_db, stream.id, result.id, broker)

    income_stream_service.delete_income_stream(test_db, stream.id, broker)

    refreshed = test_db.get(type(result), result.id)
    assert refreshed is not None
    assert refreshed.income_stream_id is None
