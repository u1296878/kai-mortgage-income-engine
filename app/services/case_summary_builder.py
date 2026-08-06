from uuid import UUID

from app.models.borrower import Borrower
from app.models.employment_calculation import EmploymentCalculation
from app.models.income_stream import IncomeStream
from app.models.nontaxable_calculation import NonTaxableCalculation
from app.models.rental_calculation import RentalCalculation
from app.models.result import Result
from app.models.self_employment_calculation import SelfEmploymentCalculation
from app.schemas.result import CaseSummaryResponse
from app.services import case_result_summary_service


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
    stream_document_ids = _stream_document_ids(results)
    saved_document_ids = _saved_document_ids(
        employment_calculations,
        rental_calculations,
        self_employment_calculations,
    )
    result_total, sources = case_result_summary_service.summarize_case_income(
        results,
        saved_document_ids,
    )
    stream_total = sum(stream.annual_income or 0.0 for stream in income_streams)
    employment_total = _included_total(employment_calculations, stream_document_ids)
    rental_total = _included_total(rental_calculations, stream_document_ids)
    nontaxable_total = sum(calc.annual_income or 0.0 for calc in nontaxable_calculations)
    self_employment_total = _included_total(self_employment_calculations, stream_document_ids)
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


def _included_total(calculations, suppressed_document_ids: set[str]) -> float:
    return sum(
        calc.annual_income or 0.0
        for calc in calculations
        if calc.included and getattr(calc, "source_document_id", None) not in suppressed_document_ids
    )


def _saved_document_ids(*calculation_groups) -> set[str]:
    return {
        calc.source_document_id
        for calculations in calculation_groups
        for calc in calculations
        if calc.included and calc.source_document_id
    }


def _stream_document_ids(results: list[Result]) -> set[str]:
    return {
        result.document_id
        for result in results
        if result.income_stream_id is not None
    }
