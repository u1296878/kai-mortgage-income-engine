from uuid import UUID, uuid4

from app.models.case import Case
from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import schedule_e_rental_service


def test_build_property_input_uses_addbacks_and_fair_rental_months():
    by_name = {field.field: field for field in property_fields("a")}

    property_input = schedule_e_rental_service.build_property_input(by_name, "a")

    year = property_input.schedule_e_years[0]
    assert year.months_in_service == 8.0
    assert year.rents_received == 13500.0
    assert year.total_expenses == 12597.0
    assert year.mortgage_interest == 5264.0
    assert year.taxes == 889.0
    assert year.depreciation_depletion == 4049.0


def test_create_drafts_persists_qualifying_rental_calculation(test_db):
    case_id = uuid4()
    broker_id = uuid4()
    document_id = uuid4()
    test_db.add(Case(id=str(case_id), broker_id=str(broker_id), title="Schedule E"))
    test_db.commit()

    calculations = schedule_e_rental_service.create_drafts_from_fields(
        test_db,
        case_id,
        broker_id,
        document_id,
        property_fields("a"),
    )

    assert len(calculations) == 1
    assert calculations[0].included is True
    assert calculations[0].source_document_id == str(document_id)
    assert calculations[0].qualifying_monthly == 1388.12
    assert calculations[0].annual_income == 16657.44


def test_create_drafts_is_idempotent_for_same_document_property(test_db):
    case_id = uuid4()
    broker_id = uuid4()
    document_id = uuid4()
    test_db.add(Case(id=str(case_id), broker_id=str(broker_id), title="Schedule E"))
    test_db.commit()

    first = schedule_e_rental_service.create_drafts_from_fields(
        test_db, case_id, broker_id, document_id, property_fields("a")
    )
    second = schedule_e_rental_service.create_drafts_from_fields(
        test_db, case_id, broker_id, document_id, property_fields("a")
    )

    assert len(first) == 1
    assert second == []


def property_fields(key):
    prefix = f"schedule_e_property_{key}"
    document_id = uuid4()
    return [
        field(f"{prefix}_address", 0.0, document_id, "2221 Corby Blvd South Bend IN 46615"),
        field(f"{prefix}_fair_rental_days", 240.0, document_id),
        field(f"{prefix}_gross_rents", 13500.0, document_id),
        field(f"{prefix}_total_expenses", 12597.0, document_id),
        field(f"{prefix}_mortgage_interest", 5264.0, document_id),
        field(f"{prefix}_taxes", 889.0, document_id),
        field(f"{prefix}_depreciation_depletion", 4049.0, document_id),
    ]


def field(name: str, value: float, document_id: UUID, raw_text: str | None = None):
    return ExtractedField(
        field=name,
        value=value,
        document_id=document_id,
        page=1,
        bounding_box=BoundingBox(x1=1, y1=1, x2=2, y2=2),
        raw_text=raw_text,
    )
