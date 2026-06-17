from uuid import uuid4

import pytest

from app.exceptions import IncomeStreamNotFound
from app.models.income_stream_type import IncomeStreamType
from app.services import income_stream_service
from tests.unit.income_stream_test_helpers import make_case, make_result, make_user


def test_create_income_stream_sets_case(test_db):
    user = make_user()
    case = make_case()
    test_db.add(case)
    test_db.commit()

    stream = income_stream_service.create_income_stream(
        test_db,
        case.id,
        "Primary job",
        IncomeStreamType.employment.value,
        "Main employer",
    )

    assert stream.case_id == case.id
    assert stream.name == "Primary job"


def test_list_income_streams_returns_case_streams(test_db):
    user = make_user()
    own_case = make_case()
    other_case = make_case(uuid4())
    test_db.add_all([own_case, other_case])
    test_db.commit()
    income_stream_service.create_income_stream(
        test_db,
        own_case.id,
        "Own stream",
        IncomeStreamType.employment.value,
        None,
    )

    other = income_stream_service.list_income_streams_by_case(test_db, other_case.id)
    assert other == []


def test_update_income_stream_changes_metadata(test_db):
    user = make_user()
    case = make_case()
    test_db.add(case)
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case.id,
        "Old",
        IncomeStreamType.other.value,
        None,
    )

    updated = income_stream_service.update_income_stream(
        test_db,
        stream.id,
        {"name": "Updated", "stream_type": IncomeStreamType.rental},
    )

    assert updated.name == "Updated"
    assert updated.stream_type == IncomeStreamType.rental.value


def test_delete_income_stream_clears_result_assignments(test_db):
    user = make_user()
    case = make_case()
    result = make_result(case.id, 85000.0)
    test_db.add_all([case, result])
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case.id,
        "To delete",
        IncomeStreamType.employment.value,
        None,
    )
    income_stream_service.assign_result_to_stream(test_db, stream.id, result.id)

    income_stream_service.delete_income_stream(test_db, stream.id)

    refreshed = test_db.get(type(result), result.id)
    assert refreshed is not None
    assert refreshed.income_stream_id is None
