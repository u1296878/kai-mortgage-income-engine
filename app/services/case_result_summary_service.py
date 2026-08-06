from app.models.result import Result
from app.schemas.extraction import ExtractedField


def summarize_case_income(
    results: list[Result],
    suppressed_document_ids: set[str] | None = None,
) -> tuple[float, list[ExtractedField]]:
    suppressed = suppressed_document_ids or set()
    total = sum(
        result.annual_income
        for result in results
        if result.annual_income is not None
        and result.document_id not in suppressed
    )
    sources = [
        ExtractedField.model_validate(field)
        for result in results
        for field in result.extracted_fields
    ]
    return total, sources
