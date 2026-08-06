from app.income.result_income import compute_result_income
from app.schemas.extraction import ExtractedField


def compute_annual_income(
    fields: list[ExtractedField],
    doc_type: str,
) -> tuple[float | None, str, str | None]:
    result = compute_result_income(
        {field.field: field.value for field in fields},
        doc_type,
    )
    return result.annual_income, result.confidence, result.notes
