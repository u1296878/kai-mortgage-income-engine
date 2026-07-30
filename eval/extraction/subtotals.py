from app.income.rental import compute_rental_income, months_from_fair_rental_days
from app.income.self_employment import compute_schedule_c
from app.schemas.extraction import ExtractedField
from app.schemas.rental_inputs import PropertyClass, RentalMethod, RentalProperty, ScheduleEYear
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear


def compute_subtotal(kind: str, by_name: dict[str, ExtractedField]) -> float | None:
    if kind == "schedule_c":
        return _schedule_c_subtotal(by_name)
    if kind == "schedule_e_property":
        return _schedule_e_annual(by_name)
    if kind == "schedule_e_properties":
        return _schedule_e_properties_annual(by_name)
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
    return _schedule_e_property_annual(by_name, "a")


def _schedule_e_properties_annual(by_name: dict[str, ExtractedField]) -> float | None:
    subtotals = [
        subtotal
        for key in ("a", "b", "c")
        if (subtotal := _schedule_e_property_annual(by_name, key)) is not None
    ]
    return round(sum(subtotals), 2) if subtotals else None


def _schedule_e_property_annual(by_name: dict[str, ExtractedField], key: str) -> float | None:
    prefix = f"schedule_e_property_{key}"
    rents = _num(by_name, f"{prefix}_gross_rents")
    expenses = _num(by_name, f"{prefix}_total_expenses")
    if rents is None and expenses is None:
        return None
    year = ScheduleEYear(
        months_in_service=months_from_fair_rental_days(_num(by_name, f"{prefix}_fair_rental_days")),
        rents_received=rents or 0.0,
        total_expenses=expenses or 0.0,
        insurance=_num(by_name, f"{prefix}_insurance") or 0.0,
        mortgage_interest=(
            (_num(by_name, f"{prefix}_mortgage_interest") or 0.0)
            + (_num(by_name, f"{prefix}_other_interest") or 0.0)
        ),
        taxes=_num(by_name, f"{prefix}_taxes") or 0.0,
        depreciation_depletion=_num(by_name, f"{prefix}_depreciation_depletion") or 0.0,
    )
    prop = RentalProperty(
        property_class=PropertyClass.primary_2_4_unit,
        method=RentalMethod.schedule_e,
        schedule_e_years=[year],
    )
    return round(compute_rental_income(prop).qualifying_monthly * 12, 2)


def _num(by_name: dict[str, ExtractedField], field: str) -> float | None:
    item = by_name.get(field)
    return item.value if item else None
