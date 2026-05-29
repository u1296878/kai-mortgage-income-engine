from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ResultNotFound
from app.models.result import Result


def save_result(db: Session, result: Result) -> Result:
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_result(db: Session, result_id: UUID) -> Result:
    result = db.get(Result, str(result_id))
    if result is None:
        raise ResultNotFound(f"Result not found: {result_id}")
    return result


def get_result_by_job(db: Session, job_id: UUID) -> Result | None:
    statement = select(Result).where(Result.job_id == str(job_id))
    return db.scalars(statement).first()


def list_results_by_case(db: Session, case_id: UUID) -> list[Result]:
    statement = select(Result).where(Result.case_id == str(case_id))
    return list(db.scalars(statement).all())


def list_results_by_income_stream(db: Session, stream_id: UUID) -> list[Result]:
    statement = select(Result).where(Result.income_stream_id == str(stream_id))
    return list(db.scalars(statement).all())


def assign_result_to_income_stream(
    db: Session,
    result_id: UUID,
    stream_id: UUID,
) -> Result:
    result = get_result(db, result_id)
    result.income_stream_id = str(stream_id)
    db.commit()
    db.refresh(result)
    return result


def clear_result_income_stream(db: Session, result_id: UUID) -> Result:
    result = get_result(db, result_id)
    result.income_stream_id = None
    db.commit()
    db.refresh(result)
    return result


def clear_income_stream_assignments(db: Session, stream_id: UUID) -> None:
    for result in list_results_by_income_stream(db, stream_id):
        result.income_stream_id = None
    db.commit()
