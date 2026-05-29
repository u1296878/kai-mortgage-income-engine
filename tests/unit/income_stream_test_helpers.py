from datetime import datetime, timezone
from uuid import uuid4

from app.models.case import Case
from app.models.result import Result
from app.models.user import User


def make_user(user_id=None, role="broker"):
    return User(
        id=str(user_id or uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="hash",
        role=role,
    )


def make_case(broker_id):
    return Case(
        id=str(uuid4()),
        broker_id=str(broker_id),
        title="Income Case",
    )


def make_result(case_id, income, confidence="medium", created_at=None):
    document_id = uuid4()
    field = {
        "field": "w2_wages",
        "value": income,
        "document_id": str(document_id),
        "page": 1,
        "bounding_box": {"x1": 1, "y1": 1, "x2": 2, "y2": 2},
    }
    return Result(
        id=str(uuid4()),
        job_id=str(uuid4()),
        document_id=str(document_id),
        case_id=str(case_id),
        doc_type="w2",
        extracted_fields=[field],
        annual_income=income,
        confidence=confidence,
        created_at=created_at or datetime.now(timezone.utc),
    )
