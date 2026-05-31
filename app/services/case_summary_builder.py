from uuid import UUID

from app.models.borrower import Borrower
from app.models.income_stream import IncomeStream
from app.models.result import Result
from app.schemas.result import CaseSummaryResponse
from app.services import income_service


def build_case_summary(
    case_id: UUID,
    borrowers: list[Borrower],
    income_streams: list[IncomeStream],
    results: list[Result],
) -> CaseSummaryResponse:
    result_total, sources = income_service.summarize_case_income(results)
    stream_total = sum(stream.annual_income or 0.0 for stream in income_streams)
    total = stream_total if income_streams else result_total
    return CaseSummaryResponse(
        case_id=case_id,
        total_annual_income=total,
        borrowers=borrowers,
        income_streams=income_streams,
        results=results,
        sources=sources,
    )
