from datetime import datetime

from app.models.result import Result
from app.schemas.extraction import ExtractedField


def compute_annual_income(
    fields: list[ExtractedField],
    doc_type: str,
) -> tuple[float | None, str, str | None]:
    values = {field.field: field.value for field in fields}
    if doc_type == "w2":
        return None, "medium", "Income derived from employment draft; W-2 boxes shown for reference only."
    if doc_type == "pay_stub":
        return None, "medium", "Income derived from employment draft; pay-stub fields shown for reference only."
    if doc_type == "tax_return":
        return None, "medium", "Income derived from per-schedule drafts; AGI shown for reference only."
    if doc_type == "bank_statement":
        return values["average_monthly_deposit"] * 12, "low", None
    if "rental_net_income" in values:
        return values["rental_net_income"], "low", None
    return values["reported_income"], "low", None


def summarize_case_income(results: list[Result]) -> tuple[float, list[ExtractedField]]:
    annual_incomes = [
        result.annual_income
        for result in results
        if result.annual_income is not None
    ]
    total = sum(annual_incomes)
    sources = [
        ExtractedField.model_validate(field)
        for result in results
        for field in result.extracted_fields
    ]
    return total, sources


def stream_income_snapshot(results: list[Result]) -> tuple[float | None, str | None]:
    selected = select_stream_result(results)
    if selected is None:
        return None, None
    return selected.annual_income, selected.confidence


def select_stream_result(results: list[Result]) -> Result | None:
    candidates = [result for result in results if result.annual_income is not None]
    if not candidates:
        return None
    return max(candidates, key=_stream_sort_key)


def _stream_sort_key(result: Result) -> tuple[int, datetime, str]:
    return (
        _confidence_rank(result.confidence),
        result.created_at,
        result.id,
    )


def _confidence_rank(confidence: str | None) -> int:
    ranks = {"high": 3, "medium": 2, "low": 1}
    return ranks.get(confidence or "", 0)
