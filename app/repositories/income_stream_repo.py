from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import IncomeStreamNotFound
from app.models.income_stream import IncomeStream


def create_income_stream(db: Session, stream: IncomeStream) -> IncomeStream:
    db.add(stream)
    db.commit()
    db.refresh(stream)
    return stream


def get_income_stream(db: Session, stream_id: UUID) -> IncomeStream:
    stream = db.get(IncomeStream, str(stream_id))
    if stream is None:
        raise IncomeStreamNotFound(f"Income stream not found: {stream_id}")
    return stream


def list_income_streams_by_case(db: Session, case_id: UUID) -> list[IncomeStream]:
    statement = select(IncomeStream).where(IncomeStream.case_id == str(case_id))
    return list(db.scalars(statement).all())


def update_income_stream(db: Session, stream_id: UUID, updates: dict) -> IncomeStream:
    stream = get_income_stream(db, stream_id)
    for field, value in updates.items():
        setattr(stream, field, value)
    db.commit()
    db.refresh(stream)
    return stream


def delete_income_stream(db: Session, stream_id: UUID) -> None:
    stream = get_income_stream(db, stream_id)
    db.delete(stream)
    db.commit()
