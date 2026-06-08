from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.income.rental import compute_rental_income, months_from_fair_rental_days
from app.models.rental_calculation import RentalCalculation
from app.repositories import rental_calculation_repo
from app.schemas.extraction import ExtractedField
from app.schemas.rental_inputs import PropertyClass, RentalMethod, RentalProperty, ScheduleEYear

PROPERTY_KEYS = ("a", "b", "c")


def create_drafts_from_fields(
    db: Session,
    case_id: UUID,
    broker_id: UUID,
    document_id: UUID,
    fields: list[ExtractedField],
) -> list[RentalCalculation]:
    by_name = {field.field: field for field in fields}
    calculations = []
    for key in PROPERTY_KEYS:
        property_input = build_property_input(by_name, key)
        if property_input is None:
            continue
        existing = rental_calculation_repo.get_by_source(db, document_id, key)
        if existing:
            continue
        result = compute_rental_income(property_input)
        calculation = RentalCalculation(
            case_id=str(case_id),
            broker_id=str(broker_id),
            label=_label(by_name, key),
            inputs=property_input.model_dump(mode="json"),
            qualifying_monthly=result.qualifying_monthly,
            annual_income=round(result.qualifying_monthly * 12, 2),
            breakdown={
                "qualifying_monthly": result.qualifying_monthly,
                "property_class": result.property_class,
                "method": result.method,
                "years": [year.__dict__ for year in result.years],
            },
            included=True,
            source_document_id=str(document_id),
            source_property_key=key,
        )
        saved = rental_calculation_repo.create(db, calculation)
        log_event(
            "schedule_e_rental_draft_created",
            {"calculation_id": saved.id, "document_id": str(document_id), "property_key": key},
        )
        calculations.append(saved)
    return calculations


def build_property_input(by_name: dict[str, ExtractedField], key: str) -> RentalProperty | None:
    prefix = f"schedule_e_property_{key}"
    if f"{prefix}_gross_rents" not in by_name and f"{prefix}_total_expenses" not in by_name:
        return None
    year = ScheduleEYear(
        months_in_service=months_from_fair_rental_days(_value(by_name, f"{prefix}_fair_rental_days")),
        rents_received=_value(by_name, f"{prefix}_gross_rents") or 0.0,
        total_expenses=_value(by_name, f"{prefix}_total_expenses") or 0.0,
        insurance=_value(by_name, f"{prefix}_insurance") or 0.0,
        mortgage_interest=(
            (_value(by_name, f"{prefix}_mortgage_interest") or 0.0)
            + (_value(by_name, f"{prefix}_other_interest") or 0.0)
        ),
        taxes=_value(by_name, f"{prefix}_taxes") or 0.0,
        depreciation_depletion=_value(by_name, f"{prefix}_depreciation_depletion") or 0.0,
    )
    return RentalProperty(
        property_class=PropertyClass.primary_2_4_unit,
        method=RentalMethod.schedule_e,
        schedule_e_years=[year],
    )


def _value(by_name: dict[str, ExtractedField], field_name: str) -> float | None:
    field = by_name.get(field_name)
    return field.value if field else None


def _label(by_name: dict[str, ExtractedField], key: str) -> str:
    field = by_name.get(f"schedule_e_property_{key}_address")
    return field.raw_text if field and field.raw_text else f"Schedule E property {key.upper()}"
