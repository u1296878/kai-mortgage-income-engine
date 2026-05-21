from datetime import datetime

from app.models.result import Result
from app.schemas.extraction import ExtractedField


def compute_annual_income(
    fields: list[ExtractedField],
    doc_type: str,
) -> tuple[float, str, str | None]:
    values = {field.field: field.value for field in fields}
    if doc_type == "w2":
        return values["w2_wages"], "high", None
    if doc_type == "pay_stub":
        annual_income = values["gross_ytd"] / datetime.now().month * 12
        notes = _pay_stub_notes(annual_income, values.get("gross_per_period"))
        return annual_income, "medium", notes
    if doc_type == "tax_return":
        return values["agi"], "high", None
    if doc_type == "bank_statement":
        return values["average_monthly_deposit"] * 12, "low", None
    return values["reported_income"], "low", None


def summarize_case_income(results: list[Result]) -> tuple[float, list[ExtractedField]]:
    annual_incomes = [
        result.annual_income
        for result in results
        if result.annual_income is not None
    ]
    total = sum(annual_incomes) / len(annual_incomes) if annual_incomes else 0.0
    sources = [
        ExtractedField.model_validate(field)
        for result in results
        for field in result.extracted_fields
    ]
    return total, sources


def _pay_stub_notes(
    annual_income: float,
    gross_per_period: float | None,
) -> str | None:
    if gross_per_period is None:
        return None
    per_period_projection = gross_per_period * 26
    variance = abs(annual_income - per_period_projection) / annual_income
    if variance > 0.2:
        return "YTD projection differs from per-period projection by more than 20%"
    return None
