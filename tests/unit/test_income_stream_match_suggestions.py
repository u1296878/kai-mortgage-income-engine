from uuid import uuid4

from app.models.income_stream import IncomeStream
from app.services import income_stream_match_service
from tests.income_stream_match_helpers import rental_fields, seed_result, w2_fields
from tests.unit.income_stream_test_helpers import make_case, make_user


def test_suggests_employment_match_for_shared_employer_name(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = make_case(broker_id)
    stream = IncomeStream(
        case_id=case.id,
        broker_id=case.broker_id,
        name="Employment: Acme Corp",
        stream_type="employment",
    )
    seed_result(test_db, case.id, "w2", w2_fields("Acme Corp"))
    test_db.add_all([case, stream])
    test_db.commit()

    suggestions = income_stream_match_service.preview_case_matches(test_db, case.id, user)

    assert str(suggestions[0].stream_id) == stream.id
    assert suggestions[0].confidence == "high"
    assert "employer" in suggestions[0].reason.lower()


def test_suggests_rental_match_for_shared_property_address(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = make_case(broker_id)
    stream = IncomeStream(
        case_id=case.id,
        broker_id=case.broker_id,
        name="Rental: 123 Sample Rental Ave",
        stream_type="rental",
    )
    seed_result(test_db, case.id, "other", rental_fields("123 Sample Rental Ave"))
    test_db.add_all([case, stream])
    test_db.commit()

    suggestion = income_stream_match_service.preview_case_matches(test_db, case.id, user)[0]

    assert str(suggestion.stream_id) == stream.id
    assert suggestion.confidence == "high"
    assert "property address" in suggestion.reason.lower()


def test_suggests_self_employment_match_for_schedule_c_result(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = make_case(broker_id)
    seed_result(
        test_db,
        case.id,
        "tax_return",
        [{"field": "schedule_c_net", "value": 25000.0, "raw_text": None}],
    )
    test_db.add(case)
    test_db.commit()

    suggestion = income_stream_match_service.preview_case_matches(test_db, case.id, user)[0]

    assert suggestion.action == "create_stream"
    assert suggestion.stream_type.value == "self_employment"
    assert suggestion.confidence == "high"


def test_does_not_cross_match_results_across_cases(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case_a = make_case(broker_id)
    case_b = make_case(broker_id)
    seed_result(test_db, case_a.id, "w2", w2_fields("Acme Corp"))
    result_b = seed_result(test_db, case_b.id, "w2", w2_fields("Other Corp"))
    test_db.add_all([case_a, case_b])
    test_db.commit()

    suggestions = income_stream_match_service.preview_case_matches(test_db, case_a.id, user)

    assert len(suggestions) == 1
    assert str(suggestions[0].result_id) != result_b.id


def test_does_not_reassign_manually_assigned_result_by_default(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = make_case(broker_id)
    stream = IncomeStream(
        case_id=case.id,
        broker_id=case.broker_id,
        name="Employment: Acme Corp",
        stream_type="employment",
    )
    test_db.add_all([case, stream])
    test_db.commit()
    seed_result(test_db, case.id, "w2", w2_fields("Acme Corp"), stream.id)

    suggestions = income_stream_match_service.preview_case_matches(test_db, case.id, user)

    assert suggestions == []


def test_auto_match_is_deterministic_for_same_input(test_db):
    broker_id = uuid4()
    user = make_user(broker_id)
    case = make_case(broker_id)
    stream = IncomeStream(
        case_id=case.id,
        broker_id=case.broker_id,
        name="Employment: Acme Corp",
        stream_type="employment",
    )
    seed_result(test_db, case.id, "w2", w2_fields("Acme Corp"))
    test_db.add_all([case, stream])
    test_db.commit()

    first = income_stream_match_service.preview_case_matches(test_db, case.id, user)
    second = income_stream_match_service.preview_case_matches(test_db, case.id, user)

    assert first == second
