from datetime import date

from app.schemas.income_inputs import (
    BasePay,
    EmploymentInput,
    EmploymentPeriod,
    VariableBucket,
)
from app.schemas.income_results import EmploymentResult
from app.services import employment_income_service


def _period(date_from, date_through, total):
    return EmploymentPeriod(
        date_from=date_from,
        date_through=date_through,
        total_earnings=total,
    )


def _empty_bucket():
    return VariableBucket(periods=[], use_ytd=True)


def _employment_with_base_and_overtime():
    base = BasePay(
        periods=[
            _period(date(2026, 1, 1), date(2026, 4, 15), 17500.0),
            _period(date(2025, 1, 1), date(2025, 12, 31), 60000.0),
        ]
    )
    overtime = VariableBucket(
        periods=[_period(date(2026, 1, 1), date(2026, 3, 31), 6000.0)],
        use_ytd=True,
    )
    return EmploymentInput(
        base_pay=base,
        overtime=overtime,
        bonus=_empty_bucket(),
        commission=_empty_bucket(),
        other=_empty_bucket(),
    )


def test_service_returns_mapped_response_model():
    employment = _employment_with_base_and_overtime()

    result = employment_income_service.calculate_employment_income(employment)

    assert isinstance(result, EmploymentResult)
    assert result.base_pay.qualifying_monthly == 5000.00
    assert result.overtime.qualifying_monthly == 2000.00
    assert result.total_monthly == 7000.00


def test_service_surfaces_per_period_breakdown():
    employment = _employment_with_base_and_overtime()

    result = employment_income_service.calculate_employment_income(employment)

    assert result.base_pay.periods[0].monthly == 5000.00
    assert result.base_pay.periods[0].pct_change == 0.00
    assert result.base_pay.periods[1].pct_change is None
