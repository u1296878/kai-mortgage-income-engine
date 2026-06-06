import pytest

from app.exceptions import InvalidRentalInput
from app.income.rental import compute_rental_income, months_from_fair_rental_days
from app.schemas.rental_inputs import (
    PropertyClass,
    RentalMethod,
    RentalProperty,
    ScheduleEYear,
)


def year(rents=0.0, months=12.0, **line_items):
    # `rents`/`months` alias the model fields; remaining line items pass through.
    return ScheduleEYear(rents_received=rents, months_in_service=months, **line_items)


def schedule_e(property_class, years, monthly_pitia=None):
    return RentalProperty(
        property_class=property_class,
        method=RentalMethod.schedule_e,
        schedule_e_years=years,
        monthly_pitia=monthly_pitia,
    )


def test_months_from_fair_rental_days_converts_days():
    assert months_from_fair_rental_days(300) == 10.0


def test_months_from_fair_rental_days_caps_at_twelve():
    assert months_from_fair_rental_days(400) == 12.0


def test_months_from_fair_rental_days_defaults_to_twelve_when_missing():
    assert months_from_fair_rental_days(None) == 12.0


def test_primary_schedule_e_two_year_annual_weighted_average():
    y1 = year(rents=24000, total_expenses=10000, insurance=1200,
              mortgage_interest=6000, taxes=3000, depreciation_depletion=4000,
              hoa_addback=500)  # annual_net 28700
    y2 = year(rents=24000, total_expenses=11000, insurance=1200,
              mortgage_interest=6000, taxes=3000, depreciation_depletion=4000)  # 27200

    result = compute_rental_income(schedule_e(PropertyClass.primary_2_4_unit, [y1, y2]))

    # (28700 + 27200) / (12 + 12) = 2329.1667
    assert result.qualifying_monthly == 2329.17
    assert result.years[0].annual_net == 28700.0


def test_primary_average_weights_by_months_not_simple_monthly_average():
    y1 = year(months=12, rents=24000)  # monthly 2000
    y2 = year(months=6, rents=18000)  # monthly 3000

    result = compute_rental_income(schedule_e(PropertyClass.primary_2_4_unit, [y1, y2]))

    # annual-weighted (42000 / 18) = 2333.33, NOT simple average (2500)
    assert result.qualifying_monthly == 2333.33
    assert result.qualifying_monthly != 2500.00


def test_investment_schedule_e_subtracts_pitia_months_weighted_net():
    y1 = year(rents=24000, total_expenses=10000, insurance=1200,
              mortgage_interest=6000, taxes=3000, depreciation_depletion=4000,
              hoa_addback=500)  # 28700
    y2 = year(rents=24000, total_expenses=11000, insurance=1200,
              mortgage_interest=6000, taxes=3000, depreciation_depletion=4000)  # 27200

    result = compute_rental_income(
        schedule_e(PropertyClass.investment, [y1, y2], monthly_pitia=1500)
    )

    # (55900 - 24*1500) / 24 = 829.1667
    assert result.qualifying_monthly == 829.17


def test_investment_net_average_weights_by_months():
    y1 = year(months=12, rents=24000)  # net monthly 2000-500
    y2 = year(months=6, rents=18000)  # net monthly 3000-500

    result = compute_rental_income(
        schedule_e(PropertyClass.investment, [y1, y2], monthly_pitia=500)
    )

    # (12*1500 + 6*2500) / 18 = 1833.33
    assert result.qualifying_monthly == 1833.33


def test_lease_primary_applies_vacancy_factor():
    prop = RentalProperty(
        property_class=PropertyClass.primary_2_4_unit,
        method=RentalMethod.lease,
        gross_monthly_rent=2000,
    )

    result = compute_rental_income(prop)

    # 2000 * (1 - 0.25)
    assert result.qualifying_monthly == 1500.00


def test_lease_investment_subtracts_pitia_after_vacancy():
    prop = RentalProperty(
        property_class=PropertyClass.investment,
        method=RentalMethod.lease,
        gross_monthly_rent=2000,
        monthly_pitia=1200,
    )

    result = compute_rental_income(prop)

    # 2000 * 0.75 - 1200
    assert result.qualifying_monthly == 300.00


def test_rental_loss_passes_through_as_negative():
    loss_year = year(rents=12000, total_expenses=30000)  # annual_net -18000

    result = compute_rental_income(
        schedule_e(PropertyClass.primary_2_4_unit, [loss_year])
    )

    assert result.qualifying_monthly == -1500.00


def test_single_year_only_uses_available_year():
    only_year = year(rents=24000, months=12)

    result = compute_rental_income(
        schedule_e(PropertyClass.primary_2_4_unit, [only_year])
    )

    assert result.qualifying_monthly == 2000.00


def test_zero_months_guards_divide_by_zero():
    idle_year = year(months=0, rents=24000)

    result = compute_rental_income(
        schedule_e(PropertyClass.primary_2_4_unit, [idle_year])
    )

    assert result.qualifying_monthly == 0.00


def test_schedule_e_without_years_raises_invalid_rental_input():
    with pytest.raises(InvalidRentalInput):
        compute_rental_income(schedule_e(PropertyClass.primary_2_4_unit, []))


def test_investment_without_pitia_raises_invalid_rental_input():
    with pytest.raises(InvalidRentalInput):
        compute_rental_income(
            schedule_e(PropertyClass.investment, [year(rents=24000)])
        )


def test_lease_without_gross_rent_raises_invalid_rental_input():
    prop = RentalProperty(
        property_class=PropertyClass.primary_2_4_unit,
        method=RentalMethod.lease,
    )

    with pytest.raises(InvalidRentalInput):
        compute_rental_income(prop)
