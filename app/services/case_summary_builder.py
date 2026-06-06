from uuid import UUID

from app.models.borrower import Borrower
from app.models.employment_calculation import EmploymentCalculation
from app.models.income_stream import IncomeStream
from app.models.result import Result
from app.schemas.result import CaseSummaryResponse
from app.services import income_service


def build_case_summary(
    case_id: UUID,
    borrowers: list[Borrower],
    income_streams: list[IncomeStream],
    results: list[Result],
    employment_calculations: list[EmploymentCalculation] | None = None,
) -> CaseSummaryResponse:
    employment_calculations = employment_calculations or []
    result_total, sources = income_service.summarize_case_income(results)
    stream_total = sum(stream.annual_income or 0.0 for stream in income_streams)
    calc_total = sum(calc.annual_income or 0.0 for calc in employment_calculations)
    # Manually-saved employment calculations add on top of document/stream income.
    # A saved calc and a stream for the same income would double-count; that is an
    # accepted, underwriter-controlled behavior for this slice (no dedupe here).
    total = (stream_total if income_streams else result_total) + calc_total
    return CaseSummaryResponse(
        case_id=case_id,
        total_annual_income=total,
        borrowers=borrowers,
        income_streams=income_streams,
        employment_calculations=employment_calculations,
        results=results,
        sources=sources,
    )
