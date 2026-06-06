from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import RentalCalculationNotFound
from app.models.rental_calculation import RentalCalculation


def create(db: Session, calculation: RentalCalculation) -> RentalCalculation:
    db.add(calculation)
    db.commit()
    db.refresh(calculation)
    return calculation


def get(db: Session, calc_id: UUID) -> RentalCalculation:
    calculation = db.get(RentalCalculation, str(calc_id))
    if calculation is None:
        raise RentalCalculationNotFound(f"Rental calculation not found: {calc_id}")
    return calculation


def list_by_case(db: Session, case_id: UUID) -> list[RentalCalculation]:
    statement = (
        select(RentalCalculation)
        .where(RentalCalculation.case_id == str(case_id))
        .order_by(RentalCalculation.created_at, RentalCalculation.id)
    )
    return list(db.scalars(statement).all())


def delete(db: Session, calc_id: UUID) -> None:
    calculation = get(db, calc_id)
    db.delete(calculation)
    db.commit()
