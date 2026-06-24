from datetime import date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.employment_calculation import EmploymentCalculation
from app.schemas.extraction import ExtractedField
from app.schemas.income_inputs import EmploymentPeriod
from app.services import employment_draft_merge

MISSING_EMPLOYER_FLAG = "Pay stub employer name is missing; verify before merging with other employment income."


def create_drafts_from_fields(
    db: Session,
    case_id: UUID,
    document_id: UUID,
    fields: list[ExtractedField],
    review_flags: list[str] | None = None,
) -> list[EmploymentCalculation]:
    by_name = {field.field: field for field in fields}
    gross_ytd = _first_value(by_name, ("paystub_gross_ytd", "gross_ytd"))
    period_end = parse_period_end(_first_text(by_name, ("paystub_period_end", "pay_date")))
    if gross_ytd is None or period_end is None:
        return []
    return employment_draft_merge.upsert_period(
        db,
        case_id,
        document_id,
        _first_text(by_name, ("paystub_employer_name", "employer_name")),
        _period(period_end, gross_ytd),
        review_flags or [],
        {
            "label_prefix": "Pay stub",
            "missing_employer_flag": MISSING_EMPLOYER_FLAG,
            "created_event": "paystub_employment_draft_created",
            "updated_event": "paystub_employment_draft_updated",
        },
    )


def parse_period_end(raw_text: str | None) -> date | None:
    if not raw_text:
        return None
    text = raw_text.strip()
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def _period(period_end: date, gross_ytd: float) -> EmploymentPeriod:
    return EmploymentPeriod(
        date_from=date(period_end.year, 1, 1),
        date_through=period_end,
        total_earnings=gross_ytd,
        included=True,
    )


def _first_value(
    by_name: dict[str, ExtractedField],
    field_names: tuple[str, ...],
) -> float | None:
    for field_name in field_names:
        field = by_name.get(field_name)
        if field and field.value is not None:
            return field.value
    return None


def _first_text(
    by_name: dict[str, ExtractedField],
    field_names: tuple[str, ...],
) -> str | None:
    for field_name in field_names:
        field = by_name.get(field_name)
        if not field:
            continue
        text = field.raw_text or str(field.value or "")
        if text.strip():
            return text.strip()
    return None
