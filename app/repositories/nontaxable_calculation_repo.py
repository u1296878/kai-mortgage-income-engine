from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NonTaxableCalculationNotFound
from app.models.nontaxable_calculation import NonTaxableCalculation


def create(db: Session, calculation: NonTaxableCalculation) -> NonTaxableCalculation:
    db.add(calculation)
    db.commit()
    db.refresh(calculation)
    return calculation


def get(db: Session, calc_id: UUID) -> NonTaxableCalculation:
    calculation = db.get(NonTaxableCalculation, str(calc_id))
    if calculation is None:
        raise NonTaxableCalculationNotFound(
            f"Non-taxable calculation not found: {calc_id}",
        )
    return calculation


def list_by_case(db: Session, case_id: UUID) -> list[NonTaxableCalculation]:
    statement = (
        select(NonTaxableCalculation)
        .where(NonTaxableCalculation.case_id == str(case_id))
        .order_by(NonTaxableCalculation.created_at, NonTaxableCalculation.id)
    )
    return list(db.scalars(statement).all())


def delete(db: Session, calc_id: UUID) -> None:
    calculation = get(db, calc_id)
    db.delete(calculation)
    db.commit()
