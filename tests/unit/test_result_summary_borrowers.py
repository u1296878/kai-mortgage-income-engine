from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.models.borrower import Borrower
from app.models.case import Case
from app.models.income_stream import IncomeStream
from app.models.result import Result
from tests.local_user_helpers import make_user
from app.services import borrower_service, income_stream_service, result_service



def test_case_summary_still_falls_back_to_stream_totals_without_borrowers(test_db):
    case_id = uuid4()
    local_user = make_user()
    case = Case(id=str(case_id), broker_id=local_user.id, title="Stream fallback")
    test_db.add(case)
    test_db.add(
        IncomeStream(
            case_id=case.id,
            broker_id=case.broker_id,
            name="Employment",
            stream_type="employment",
            annual_income=93000.0,
            confidence="high",
        ),
    )
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, local_user)

    assert summary.total_annual_income == 93000.0
    assert summary.borrowers == []


def test_case_summary_includes_borrowers_when_present(test_db):
    case_id = uuid4()
    local_user = make_user()
    case = Case(id=str(case_id), broker_id=local_user.id, title="Borrowers")
    test_db.add(case)
    test_db.add(
        Borrower(
            case_id=case.id,
            broker_id=case.broker_id,
            first_name="Alex",
            last_name="Smith",
            role="primary",
        ),
    )
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, local_user)

    assert len(summary.borrowers) == 1
    assert summary.borrowers[0].first_name == "Alex"


def test_case_summary_does_not_double_count_after_borrower_assignment(test_db):
    case_id = uuid4()
    broker_id = uuid4()
    broker = make_user(broker_id)
    case = Case(id=str(case_id), broker_id=str(broker_id), title="Borrower stream")
    first = _manual_result(
        case.id,
        85000.0,
        "high",
        datetime.now(timezone.utc) - timedelta(days=1),
    )
    second = _manual_result(case.id, 87000.0, "high", datetime.now(timezone.utc))
    test_db.add(case)
    test_db.add_all([first, second])
    test_db.commit()
    stream = income_stream_service.create_income_stream(
        test_db,
        case_id,
        "Employment",
        "employment",
        None,
        broker,
    )
    borrower = borrower_service.create_borrower(
        test_db,
        case_id,
        "Alex",
        "Smith",
        "primary",
        broker,
    )
    income_stream_service.assign_result_to_stream(test_db, UUID(stream.id), UUID(first.id), broker)
    income_stream_service.assign_result_to_stream(test_db, UUID(stream.id), UUID(second.id), broker)
    borrower_service.assign_income_stream_to_borrower(
        test_db,
        UUID(borrower.id),
        UUID(stream.id),
        broker,
    )

    summary = result_service.get_case_summary(test_db, case_id, broker)

    assert summary.total_annual_income == 87000.0


def _manual_result(case_id, annual_income, confidence, created_at):
    document_id = uuid4()
    fields = [
        {
            "field": "w2_wages",
            "value": annual_income,
            "document_id": str(document_id),
            "page": 1,
            "bounding_box": {"x1": 1, "y1": 1, "x2": 2, "y2": 2},
        }
    ]
    return Result(
        id=str(uuid4()),
        job_id=str(uuid4()),
        document_id=str(document_id),
        case_id=str(case_id),
        doc_type="w2",
        extracted_fields=fields,
        annual_income=annual_income,
        confidence=confidence,
        created_at=created_at,
    )
