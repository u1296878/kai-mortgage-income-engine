from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import SelfEmploymentCalculationNotFound
from app.models.self_employment_calculation import SelfEmploymentCalculation


def create(
    db: Session,
    calculation: SelfEmploymentCalculation,
) -> SelfEmploymentCalculation:
    db.add(calculation)
    db.commit()
    db.refresh(calculation)
    return calculation


def get(db: Session, calc_id: UUID) -> SelfEmploymentCalculation:
    calculation = db.get(SelfEmploymentCalculation, str(calc_id))
    if calculation is None:
        raise SelfEmploymentCalculationNotFound(
            f"Self-employment calculation not found: {calc_id}",
        )
    return calculation


def list_by_case(db: Session, case_id: UUID) -> list[SelfEmploymentCalculation]:
    statement = (
        select(SelfEmploymentCalculation)
        .where(SelfEmploymentCalculation.case_id == str(case_id))
        .order_by(SelfEmploymentCalculation.created_at, SelfEmploymentCalculation.id)
    )
    return list(db.scalars(statement).all())


def get_by_source(
    db: Session,
    document_id: UUID,
    source_business_key: str,
) -> SelfEmploymentCalculation | None:
    statement = select(SelfEmploymentCalculation).where(
        SelfEmploymentCalculation.source_document_id == str(document_id),
        SelfEmploymentCalculation.source_business_key == source_business_key,
    )
    return db.scalars(statement).first()


def update(
    db: Session,
    calculation: SelfEmploymentCalculation,
) -> SelfEmploymentCalculation:
    db.add(calculation)
    db.commit()
    db.refresh(calculation)
    return calculation


def delete(db: Session, calc_id: UUID) -> None:
    calculation = get(db, calc_id)
    db.delete(calculation)
    db.commit()
