from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import EmploymentCalculationNotFound
from app.models.employment_calculation import EmploymentCalculation


def create(db: Session, calculation: EmploymentCalculation) -> EmploymentCalculation:
    db.add(calculation)
    db.commit()
    db.refresh(calculation)
    return calculation


def get(db: Session, calc_id: UUID) -> EmploymentCalculation:
    calculation = db.get(EmploymentCalculation, str(calc_id))
    if calculation is None:
        raise EmploymentCalculationNotFound(f"Employment calculation not found: {calc_id}")
    return calculation


def list_by_case(db: Session, case_id: UUID) -> list[EmploymentCalculation]:
    statement = (
        select(EmploymentCalculation)
        .where(EmploymentCalculation.case_id == str(case_id))
        .order_by(EmploymentCalculation.created_at, EmploymentCalculation.id)
    )
    return list(db.scalars(statement).all())


def delete(db: Session, calc_id: UUID) -> None:
    calculation = get(db, calc_id)
    db.delete(calculation)
    db.commit()
