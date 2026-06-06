from datetime import datetime, timezone
from uuid import uuid4

from app.models.case import Case
from app.models.income_stream import IncomeStream
from app.models.result import Result
from app.models.user import User
from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import result_service


def make_user(user_id=None, role="broker"):
    return User(
        id=str(user_id or uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="hash",
        role=role,
    )


def make_field(field: str = "w2_wages", value: float = 85000.00) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
    )


def test_get_case_summary_returns_total_and_sources(test_db):
    case_id = uuid4()
    manager = make_user(role="manager")
    test_db.add(Case(id=str(case_id), broker_id=str(uuid4()), title="Smith Purchase"))
    test_db.commit()
    first = result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        case_id,
        "w2",
        [make_field("w2_wages", 85000.00)],
    )
    second = result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        case_id,
        "tax_return",
        [make_field("agi", 79000.00)],
    )
    # Results are ordered by created_at; pin distinct values so the source
    # order is well-defined regardless of clock resolution on fast inserts.
    first.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    second.created_at = datetime(2024, 1, 2, tzinfo=timezone.utc)
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, manager)

    assert summary.total_annual_income == 164000.00
    assert [source.field for source in summary.sources] == ["w2_wages", "agi"]


def test_case_summary_uses_stream_totals_when_streams_exist(test_db):
    case_id = uuid4()
    manager = make_user(role="manager")
    case = Case(id=str(case_id), broker_id=str(uuid4()), title="Smith Purchase")
    test_db.add(case)
    test_db.commit()
    result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        case_id,
        "w2",
        [make_field("w2_wages", 85000.00)],
    )
    result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        case_id,
        "tax_return",
        [make_field("agi", 79000.00)],
    )
    stream = IncomeStream(
        case_id=case.id,
        broker_id=case.broker_id,
        name="Employment",
        stream_type="employment",
        annual_income=87000.0,
        confidence="high",
    )
    test_db.add(stream)
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, manager)

    assert summary.total_annual_income == 87000.0
    assert len(summary.income_streams) == 1


def test_case_summary_falls_back_to_result_totals_when_no_streams_exist(test_db):
    case_id = uuid4()
    manager = make_user(role="manager")
    case = Case(id=str(case_id), broker_id=str(uuid4()), title="Fallback")
    test_db.add(case)
    test_db.commit()
    result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        case_id,
        "w2",
        [make_field("w2_wages", 60000.00)],
    )
    result_service.save_extraction_result(
        test_db,
        uuid4(),
        uuid4(),
        case_id,
        "tax_return",
        [make_field("agi", 50000.00)],
    )

    summary = result_service.get_case_summary(test_db, case_id, manager)

    assert summary.total_annual_income == 110000.0
    assert summary.income_streams == []


def test_case_summary_does_not_double_count_multiple_results_in_same_stream(test_db):
    case_id = uuid4()
    manager = make_user(role="manager")
    case = Case(id=str(case_id), broker_id=str(uuid4()), title="No Double Count")
    test_db.add(case)
    test_db.add_all([
        _manual_result(case.id, 85000.0, "high"),
        _manual_result(case.id, 87000.0, "high"),
    ])
    stream = IncomeStream(
        case_id=case.id,
        broker_id=case.broker_id,
        name="Employment",
        stream_type="employment",
        annual_income=87000.0,
        confidence="high",
    )
    test_db.add(stream)
    test_db.commit()

    summary = result_service.get_case_summary(test_db, case_id, manager)

    assert summary.total_annual_income == 87000.0


def _manual_result(case_id, annual_income, confidence):
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
    )
