from uuid import uuid4

from app.models.case import Case
from app.repositories import self_employment_calculation_repo
from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import result_service, schedule_c_se_service


def make_field(
    field: str,
    value: float | None,
    document_id,
    raw_text: str | None = None,
) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=document_id,
        page=1,
        bounding_box=BoundingBox(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
        raw_text=raw_text,
    )


def test_single_business_years_average_in_one_schedule_c_calculation(test_db):
    case_id = uuid4()
    doc_2023 = uuid4()
    doc_2024 = uuid4()
    test_db.add(Case(id=str(case_id), title="Hendrickson"))
    test_db.commit()

    first = schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2023,
        _schedule_c_fields(doc_2023, 2023, 94380, 3633, 4628),
    )
    second = schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2024,
        _schedule_c_fields(doc_2024, 2024, 85247, 659, 3173),
    )
    summary = result_service.get_case_summary(test_db, case_id)

    assert len(first) == 1
    assert len(second) == 1
    assert len(summary.self_employment_calculations) == 1
    calculation = summary.self_employment_calculations[0]
    assert calculation.qualifying_monthly == 7988.33
    assert calculation.annual_income == 95859.96
    assert summary.total_annual_income == 95859.96


def test_single_schedule_c_per_return_matches_without_business_name(test_db):
    case_id = uuid4()
    doc_2023 = uuid4()
    doc_2024 = uuid4()

    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2023,
        _schedule_c_fields(doc_2023, 2023, 12000, 0, 0, business_name=None),
    )
    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2024,
        _schedule_c_fields(doc_2024, 2024, 24000, 0, 0, business_name=None),
    )
    calculations = self_employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(calculations) == 1
    assert calculations[0].qualifying_monthly == 1500.0


def test_business_name_variations_match_across_tax_years(test_db):
    case_id = uuid4()
    doc_2023 = uuid4()
    doc_2024 = uuid4()

    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2023,
        _schedule_c_fields(doc_2023, 2023, 12000, 0, 0, "Law Office of David S. Hendri"),
    )
    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2024,
        _schedule_c_fields(doc_2024, 2024, 24000, 0, 0, "Law Offices of David S. Hendrickson"),
    )
    calculations = self_employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(calculations) == 1
    assert calculations[0].qualifying_monthly == 1500.0


def test_different_named_businesses_do_not_average(test_db):
    case_id = uuid4()
    doc_2023 = uuid4()
    doc_2024 = uuid4()

    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2023,
        _schedule_c_fields(doc_2023, 2023, 12000, 0, 0, "Johnson Plumbing"),
    )
    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        doc_2024,
        _schedule_c_fields(doc_2024, 2024, 24000, 0, 0, "Hendrickson Law"),
    )
    calculations = self_employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(calculations) == 2
    assert sum(calc.annual_income for calc in calculations) == 36000.0


def test_two_businesses_in_same_return_stay_separate_and_sum(test_db):
    case_id = uuid4()
    document_id = uuid4()

    schedule_c_se_service.create_drafts_from_fields(
        test_db,
        case_id,
        document_id,
        [
            make_field("tax_year", 2024.0, document_id),
            make_field("schedule_c_business_1_business_name", 0.0, document_id, "Alpha Consulting"),
            make_field("schedule_c_business_1_net_profit", 12000.0, document_id),
            make_field("schedule_c_business_2_business_name", 0.0, document_id, "Beta Repair"),
            make_field("schedule_c_business_2_net_profit", 24000.0, document_id),
        ],
    )
    calculations = self_employment_calculation_repo.list_by_case(test_db, case_id)

    assert len(calculations) == 2
    assert sum(calc.annual_income for calc in calculations) == 36000.0


def _schedule_c_fields(
    document_id,
    tax_year: int,
    net_profit: float,
    depreciation: float,
    home: float,
    business_name: str | None = "Law Office of David S. Hendrickson",
):
    fields = [
        make_field("tax_year", float(tax_year), document_id),
        make_field("schedule_c_business_1_net_profit", net_profit, document_id),
        make_field("schedule_c_business_1_depreciation", depreciation, document_id),
        make_field("schedule_c_business_1_business_use_of_home", home, document_id),
    ]
    if business_name:
        fields.append(
            make_field("schedule_c_business_1_business_name", 0.0, document_id, business_name)
        )
    return fields
