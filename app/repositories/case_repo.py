from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import CaseNotFound
from app.models.case import Case


def create_case(db: Session, case: Case) -> Case:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: UUID) -> Case:
    case = db.get(Case, str(case_id))
    if case is None:
        raise CaseNotFound(f"Case not found: {case_id}")
    return case


def find_case(db: Session, case_id: UUID) -> Case | None:
    return db.get(Case, str(case_id))


def list_cases(db: Session) -> list[Case]:
    return list(db.scalars(select(Case)).all())


def update_case(db: Session, case_id: UUID, updates: dict) -> Case:
    case = get_case(db, case_id)
    for field, value in updates.items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return case


def delete_case(db: Session, case_id: UUID) -> None:
    case = get_case(db, case_id)
    db.delete(case)
    db.commit()
