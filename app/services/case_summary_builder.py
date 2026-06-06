from uuid import UUID

from app.models.borrower import Borrower
from app.models.employment_calculation import EmploymentCalculation
from app.models.income_stream import IncomeStream
from app.models.rental_calculation import RentalCalculation
from app.models.result import Result
from app.schemas.result import CaseSummaryResponse
from app.services import income_service


def build_case_summary(
    case_id: UUID,
    borrowers: list[Borrower],
    income_streams: list[IncomeStream],
    results: list[Result],
    employment_calculations: list[EmploymentCalculation] | None = None,
    rental_calculations: list[RentalCalculation] | None = None,
) -> CaseSummaryResponse:
    employment_calculations = employment_calculations or []
    rental_calculations = rental_calculations or []
    result_total, sources = income_service.summarize_case_income(results)
    stream_total = sum(stream.annual_income or 0.0 for stream in income_streams)
    employment_total = sum(calc.annual_income or 0.0 for calc in employment_calculations)
    rental_total = sum(calc.annual_income or 0.0 for calc in rental_calculations)
    # Manually-saved employment and rental calculations add on top of document/stream
    # income. A rental loss (negative annual_income) reduces the total — correct.
    # A saved calc and a stream for the same income would double-count; that is an
    # accepted, underwriter-controlled behavior for this slice (no dedupe here).
    total = (stream_total if income_streams else result_total) + employment_total + rental_total
    return CaseSummaryResponse(
        case_id=case_id,
        total_annual_income=total,
        borrowers=borrowers,
        income_streams=income_streams,
        employment_calculations=employment_calculations,
        rental_calculations=rental_calculations,
        results=results,
        sources=sources,
    )
