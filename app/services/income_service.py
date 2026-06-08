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
        return _compute_pay_stub_income(fields, values)
    if doc_type == "tax_return":
        return _compute_tax_return_income(values)
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


def _compute_pay_stub_income(
    fields: list[ExtractedField],
    values: dict[str, float],
) -> tuple[float, str, str | None]:
    period_income = _period_based_income(fields, values)
    if "gross_ytd" in values:
        annual_income = values["gross_ytd"] / datetime.now().month * 12
        notes = _pay_stub_notes(annual_income, period_income)
        confidence = "medium" if notes else "high"
        return annual_income, confidence, notes
    if period_income is not None:
        return period_income, "low", None
    return 0.0, "low", "No gross income fields found"


def _compute_tax_return_income(values: dict[str, float]) -> tuple[float, str, str | None]:
    if "schedule_e_present" in values and "total_income" in values:
        return values["total_income"], "high", _schedule_e_notes(values)
    if "agi" in values:
        return values["agi"], "high", None
    return values["total_income"], "medium", "AGI not found; using Form 1040 total income"


def _schedule_e_notes(values: dict[str, float]) -> str:
    net_option = values["total_income"]
    gross_rents = _schedule_e_gross_rents(values)
    net_rental = values.get("schedule_e_net_rental_income")
    if gross_rents is None or net_rental is None:
        return f"Schedule E detected. Net rental option: ${net_option:,.2f}."
    gross_option = round(net_option - net_rental + gross_rents, 2)
    return (
        f"Schedule E detected. Net rental option: ${net_option:,.2f}; "
        f"gross rental receipts option: ${gross_option:,.2f}."
    )


def _schedule_e_gross_rents(values: dict[str, float]) -> float | None:
    if "schedule_e_gross_rents_total" in values:
        return values["schedule_e_gross_rents_total"]
    property_rents = [
        value
        for field, value in values.items()
        if field.startswith("schedule_e_property_") and field.endswith("_gross_rents")
    ]
    return sum(property_rents) if property_rents else None


def _period_based_income(
    fields: list[ExtractedField],
    values: dict[str, float],
) -> float | None:
    multiplier = _period_multiplier(fields)
    if multiplier is None or "gross_this_period" not in values:
        return None
    return values["gross_this_period"] * multiplier


def _period_multiplier(fields: list[ExtractedField]) -> int | None:
    multipliers = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12}
    period = next((field.raw_text for field in fields if field.field == "pay_period_type"), None)
    return multipliers.get(period or "")


def _pay_stub_notes(annual_income: float, period_income: float | None) -> str | None:
    if period_income is None or annual_income == 0:
        return None
    variance = abs(annual_income - period_income) / annual_income
    if variance > 0.2:
        return f"YTD and period-based projections differ by {variance:.0%}"
    return None


def _stream_sort_key(result: Result) -> tuple[int, datetime, str]:
    return (
        _confidence_rank(result.confidence),
        result.created_at,
        result.id,
    )


def _confidence_rank(confidence: str | None) -> int:
    ranks = {"high": 3, "medium": 2, "low": 1}
    return ranks.get(confidence or "", 0)
