from app.income.rental import compute_rental_income
from app.income.self_employment import compute_schedule_c
from app.schemas.extraction import ExtractedField
from app.schemas.rental_inputs import PropertyClass, RentalMethod, RentalProperty, ScheduleEYear
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear


def compute_subtotal(kind: str, by_name: dict[str, ExtractedField]) -> float | None:
    if kind == "schedule_c":
        return _schedule_c_subtotal(by_name)
    if kind == "schedule_e_property":
        return _schedule_e_annual(by_name)
    return None


def _schedule_c_subtotal(by_name: dict[str, ExtractedField]) -> float | None:
    net = _num(by_name, "schedule_c_net_profit")
    if net is None:
        return None
    year = ScheduleCYear(
        tax_year=int(_num(by_name, "tax_year") or 0) or None,
        net_profit=net,
        nonrecurring_income=_num(by_name, "schedule_c_nonrecurring_income") or 0.0,
        depletion=_num(by_name, "schedule_c_depletion") or 0.0,
        depreciation=_num(by_name, "schedule_c_depreciation") or 0.0,
        meals_entertainment_exclusion=_num(by_name, "schedule_c_meals_exclusion") or 0.0,
        business_use_of_home=_num(by_name, "schedule_c_business_use_of_home") or 0.0,
        business_miles=_num(by_name, "schedule_c_business_miles") or 0.0,
        amortization_casualty=_num(by_name, "schedule_c_amortization_casualty") or 0.0,
    )
    return compute_schedule_c(ScheduleCInput(years=[year])).years[0].annual_subtotal


def _schedule_e_annual(by_name: dict[str, ExtractedField]) -> float | None:
    rents = _num(by_name, "schedule_e_property_a_rents_received")
    expenses = _num(by_name, "schedule_e_property_a_total_expenses")
    if rents is None or expenses is None:
        return None
    year = ScheduleEYear(
        months_in_service=12,
        rents_received=rents,
        total_expenses=expenses,
        insurance=_num(by_name, "schedule_e_property_a_insurance") or 0.0,
        mortgage_interest=_num(by_name, "schedule_e_property_a_mortgage_interest") or 0.0,
        taxes=_num(by_name, "schedule_e_property_a_taxes") or 0.0,
        depreciation_depletion=_num(by_name, "schedule_e_property_a_depreciation_depletion") or 0.0,
        hoa_addback=_num(by_name, "schedule_e_property_a_hoa_addback") or 0.0,
        casualty_one_time=_num(by_name, "schedule_e_property_a_casualty_one_time") or 0.0,
    )
    prop = RentalProperty(
        property_class=PropertyClass.investment,
        method=RentalMethod.schedule_e,
        monthly_pitia=0.0,
        schedule_e_years=[year],
    )
    return compute_rental_income(prop).qualifying_monthly * 12


def _num(by_name: dict[str, ExtractedField], field: str) -> float | None:
    item = by_name.get(field)
    return item.value if item else None
