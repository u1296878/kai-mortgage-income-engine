from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.result import Result
from app.services import income_service


def make_result(income, confidence, created_at):
    document_id = uuid4()
    return Result(
        id=str(uuid4()),
        job_id=str(uuid4()),
        document_id=str(document_id),
        case_id=str(uuid4()),
        doc_type="w2",
        extracted_fields=[
            {
                "field": "w2_wages",
                "value": income,
                "document_id": str(document_id),
                "page": 1,
                "bounding_box": {"x1": 1, "y1": 1, "x2": 2, "y2": 2},
            }
        ],
        annual_income=income,
        confidence=confidence,
        created_at=created_at,
    )


def test_stream_income_high_confidence_beats_medium_and_low():
    now = datetime.now(timezone.utc)
    low = make_result(60000.0, "low", now - timedelta(days=2))
    medium = make_result(70000.0, "medium", now - timedelta(days=1))
    high = make_result(65000.0, "high", now)

    annual_income, confidence = income_service.stream_income_snapshot([low, medium, high])

    assert annual_income == 65000.0
    assert confidence == "high"


def test_stream_income_medium_confidence_beats_low():
    now = datetime.now(timezone.utc)
    low = make_result(60000.0, "low", now - timedelta(days=1))
    medium = make_result(55000.0, "medium", now)

    annual_income, confidence = income_service.stream_income_snapshot([low, medium])

    assert annual_income == 55000.0
    assert confidence == "medium"


def test_stream_income_tied_confidence_uses_most_recent_result():
    now = datetime.now(timezone.utc)
    older = make_result(61000.0, "high", now - timedelta(days=1))
    newer = make_result(62000.0, "high", now)

    annual_income, confidence = income_service.stream_income_snapshot([older, newer])

    assert annual_income == 62000.0
    assert confidence == "high"
