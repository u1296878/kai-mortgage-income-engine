from uuid import uuid4

from app.models.income_stream import IncomeStream
from app.models.result import Result
from app.services import income_stream_match_service
from tests.income_stream_match_helpers import seed_result, w2_fields
from tests.unit.income_stream_test_helpers import make_case, make_user


def test_high_confidence_match_can_be_applied(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = make_case(broker_id)
    stream = IncomeStream(
        case_id=case.id,
        broker_id=case.broker_id,
        name="Employment: Acme Corp",
        stream_type="employment",
    )
    result = seed_result(test_db, case.id, "w2", w2_fields("Acme Corp"))
    test_db.add_all([case, stream])
    test_db.commit()

    _, applied_count, _ = income_stream_match_service.apply_case_matches(test_db, case.id, user)

    refreshed = test_db.get(Result, result.id)
    assert applied_count == 1
    assert refreshed.income_stream_id == stream.id


def test_low_confidence_match_is_not_auto_applied(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = make_case(broker_id)
    result = seed_result(
        test_db,
        case.id,
        "pay_stub",
        [{"field": "gross_ytd", "value": 62000.0, "raw_text": None}],
    )
    test_db.add(case)
    test_db.commit()

    suggestions, applied_count, created_count = income_stream_match_service.apply_case_matches(
        test_db,
        case.id,
        user,
    )

    refreshed = test_db.get(Result, result.id)
    assert suggestions[0].confidence == "medium"
    assert applied_count == 0
    assert created_count == 0
    assert refreshed.income_stream_id is None


def test_same_case_validation_blocks_cross_case_assignment(test_db):
    broker_id = uuid4()
    local_user = make_user(broker_id)
    case_a = make_case(broker_id)
    case_b = make_case(broker_id)
    stream_b = IncomeStream(
        case_id=case_b.id,
        broker_id=case_b.broker_id,
        name="Employment: Acme Corp",
        stream_type="employment",
    )
    result_a = seed_result(test_db, case_a.id, "w2", w2_fields("Acme Corp"))
    test_db.add_all([case_a, case_b, stream_b])
    test_db.commit()

    _, applied_count, created_count = income_stream_match_service.apply_case_matches(
        test_db,
        case_a.id,
        local_user,
    )

    refreshed = test_db.get(Result, result_a.id)
    assert applied_count == 1
    assert created_count == 1
    assert refreshed.income_stream_id != stream_b.id
