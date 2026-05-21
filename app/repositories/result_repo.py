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
