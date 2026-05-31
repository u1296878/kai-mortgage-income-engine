from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import BorrowerNotFound
from app.models.borrower import Borrower


def create_borrower(db: Session, borrower: Borrower) -> Borrower:
    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower


def get_borrower(db: Session, borrower_id: UUID) -> Borrower:
    borrower = db.get(Borrower, str(borrower_id))
    if borrower is None:
        raise BorrowerNotFound(f"Borrower not found: {borrower_id}")
    return borrower


def list_borrowers_by_case(db: Session, case_id: UUID) -> list[Borrower]:
    statement = (
        select(Borrower)
        .where(Borrower.case_id == str(case_id))
        .order_by(Borrower.created_at, Borrower.id)
    )
    return list(db.scalars(statement).all())


def update_borrower(db: Session, borrower_id: UUID, updates: dict) -> Borrower:
    borrower = get_borrower(db, borrower_id)
    for field, value in updates.items():
        setattr(borrower, field, value)
    db.commit()
    db.refresh(borrower)
    return borrower


def delete_borrower(db: Session, borrower_id: UUID) -> None:
    borrower = get_borrower(db, borrower_id)
    db.delete(borrower)
    db.commit()
