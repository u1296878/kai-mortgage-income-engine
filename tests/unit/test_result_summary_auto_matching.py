from uuid import uuid4

from app.models.case import Case
from app.models.result import Result
from app.models.user import User
from app.services import income_stream_match_service, result_service


def make_user(user_id=None, role="broker"):
    return User(
        id=str(user_id or uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="hash",
        role=role,
    )


def test_case_summary_does_not_double_count_after_auto_matching(test_db):
    broker_id = uuid4()
    broker = make_user(broker_id)
    manager = make_user(role="manager")
    case = Case(id=str(uuid4()), broker_id=str(broker_id), title="Auto match")
    test_db.add(case)
    test_db.commit()
    first = _employment_result(case.id, 85000.0, "high", "Acme Corp")
    second = _employment_result(case.id, 87000.0, "medium", "Acme Corp")
    test_db.add_all([first, second])
    test_db.commit()

    income_stream_match_service.apply_case_matches(test_db, case.id, broker)
    summary = result_service.get_case_summary(test_db, case.id, manager)

    assert summary.total_annual_income == 85000.0


def _employment_result(case_id, annual_income, confidence, employer):
    document_id = uuid4()
    return Result(
        id=str(uuid4()),
        job_id=str(uuid4()),
        document_id=str(document_id),
        case_id=str(case_id),
        doc_type="w2",
        extracted_fields=[
            {
                "field": "w2_wages",
                "value": annual_income,
                "document_id": str(document_id),
                "page": 1,
                "bounding_box": {"x1": 1, "y1": 1, "x2": 2, "y2": 2},
            },
            {
                "field": "w2_employer_name",
                "value": 0.0,
                "document_id": str(document_id),
                "page": 1,
                "bounding_box": {"x1": 1, "y1": 1, "x2": 2, "y2": 2},
                "raw_text": employer,
            },
        ],
        annual_income=annual_income,
        confidence=confidence,
    )
