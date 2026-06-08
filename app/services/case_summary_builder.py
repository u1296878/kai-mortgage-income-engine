from uuid import UUID

from app.models.borrower import Borrower
from app.models.employment_calculation import EmploymentCalculation
from app.models.income_stream import IncomeStream
from app.models.nontaxable_calculation import NonTaxableCalculation
from app.models.rental_calculation import RentalCalculation
from app.models.result import Result
from app.models.self_employment_calculation import SelfEmploymentCalculation
from app.schemas.result import CaseSummaryResponse
from app.services import income_service


def build_case_summary(
    case_id: UUID,
    borrowers: list[Borrower],
    income_streams: list[IncomeStream],
    results: list[Result],
    employment_calculations: list[EmploymentCalculation] | None = None,
    rental_calculations: list[RentalCalculation] | None = None,
    nontaxable_calculations: list[NonTaxableCalculation] | None = None,
    self_employment_calculations: list[SelfEmploymentCalculation] | None = None,
) -> CaseSummaryResponse:
    employment_calculations = employment_calculations or []
    rental_calculations = rental_calculations or []
    nontaxable_calculations = nontaxable_calculations or []
    self_employment_calculations = self_employment_calculations or []
    result_total, sources = income_service.summarize_case_income(results)
    stream_total = sum(stream.annual_income or 0.0 for stream in income_streams)
    employment_total = sum(calc.annual_income or 0.0 for calc in employment_calculations)
    rental_total = sum(
        calc.annual_income or 0.0
        for calc in rental_calculations
        if calc.included
    )
    nontaxable_total = sum(calc.annual_income or 0.0 for calc in nontaxable_calculations)
    self_employment_total = sum(
        calc.annual_income or 0.0 for calc in self_employment_calculations
    )
    # Saved worksheet calculations are additive and can double-count if an
    # underwriter also keeps the same income in a stream; no dedupe in this slice.
    total = (
        (stream_total if income_streams else result_total)
        + employment_total
        + rental_total
        + nontaxable_total
        + self_employment_total
    )
    return CaseSummaryResponse(
        case_id=case_id,
        total_annual_income=total,
        borrowers=borrowers,
        income_streams=income_streams,
        employment_calculations=employment_calculations,
        rental_calculations=rental_calculations,
        nontaxable_calculations=nontaxable_calculations,
        self_employment_calculations=self_employment_calculations,
        results=results,
        sources=sources,
    )
