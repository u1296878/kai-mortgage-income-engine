from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.employment_calculation import EmploymentCalculation
from app.schemas.extraction import ExtractedField
from app.schemas.income_inputs import EmploymentPeriod
from app.services import employment_draft_merge

MISSING_EMPLOYER_FLAG = "W-2 employer name is missing; verify before merging with other W-2 income."


def create_drafts_from_fields(
    db: Session,
    case_id: UUID,
    document_id: UUID,
    fields: list[ExtractedField],
    review_flags: list[str] | None = None,
) -> list[EmploymentCalculation]:
    by_name = {field.field: field for field in fields}
    wages = _value(by_name, "w2_wages")
    tax_year = _tax_year(by_name)
    if wages is None or tax_year is None:
        return []
    return employment_draft_merge.upsert_period(
        db,
        case_id,
        document_id,
        _text(by_name, "w2_employer_name"),
        _period(tax_year, wages),
        review_flags or [],
        {
            "label_prefix": "W-2",
            "missing_employer_flag": MISSING_EMPLOYER_FLAG,
            "created_event": "w2_employment_draft_created",
            "updated_event": "w2_employment_draft_updated",
        },
    )


def _period(tax_year: int, wages: float) -> EmploymentPeriod:
    return EmploymentPeriod(
        date_from=date(tax_year, 1, 1),
        date_through=date(tax_year, 12, 31),
        total_earnings=wages,
        included=True,
    )


def _tax_year(by_name: dict[str, ExtractedField]) -> int | None:
    value = _value(by_name, "tax_year")
    if value is None:
        value = _value(by_name, "w2_tax_year")
    return int(value) if value is not None else None


def _value(by_name: dict[str, ExtractedField], field_name: str) -> float | None:
    field = by_name.get(field_name)
    return field.value if field else None


def _text(by_name: dict[str, ExtractedField], field_name: str) -> str | None:
    field = by_name.get(field_name)
    if field is None:
        return None
    text = field.raw_text or str(field.value or "")
    return text.strip() or None
