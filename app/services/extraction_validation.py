from typing import Literal, TypedDict

from app.config import settings
from app.schemas.extraction import ExtractedField

Severity = Literal["high", "low"]


class ValidationIssue(TypedDict):
    fields: list[str]
    message: str
    severity: Severity


def validate_extraction(
    doc_type: str,
    fields: list[ExtractedField],
) -> list[ValidationIssue]:
    by_name = {field.field: field for field in fields}
    issues = [
        _coerce_issue(issue)
        for field in fields
        for issue in field.review_flags
    ]
    issues.extend([
        _issue([field.field], f"{field.field} has low model confidence.", "low")
        for field in fields
        if field.confidence < settings.extraction_confidence_threshold
        and field.value is not None
    ])
    if doc_type == "w2":
        issues.extend(_validate_w2(by_name))
    if doc_type == "tax_return":
        issues.extend(_validate_tax_return(by_name))
    return issues


def has_high_issue(issues: list[ValidationIssue]) -> bool:
    return any(issue["severity"] == "high" for issue in issues)


def schedule_c_issue_messages(issues: list[ValidationIssue]) -> list[str]:
    return [
        issue["message"]
        for issue in issues
        if any(field.startswith("schedule_c") for field in issue["fields"])
    ]


def w2_issue_messages(issues: list[ValidationIssue]) -> list[str]:
    return [
        issue["message"]
        for issue in issues
        if any(field.startswith("w2_") for field in issue["fields"])
    ]


def _validate_w2(by_name: dict[str, ExtractedField]) -> list[ValidationIssue]:
    issues = []
    wages = _value(by_name, "w2_wages")
    withholding = _value(by_name, "w2_federal_tax_withheld")
    if wages is None or wages <= 0:
        issues.append(_issue(["w2_wages"], "W-2 Box 1 wages are missing or zero.", "high"))
    if wages is not None and withholding is not None and withholding > wages:
        issues.append(
            _issue(
                ["w2_federal_tax_withheld", "w2_wages"],
                "W-2 Box 2 federal withholding exceeds Box 1 wages.",
                "high",
            )
        )
    for field_name in ("w2_social_security_wages", "w2_medicare_wages"):
        value = _value(by_name, field_name)
        if wages is not None and wages > 0 and value is not None and not 0.5 * wages <= value <= 2 * wages:
            issues.append(
                _issue(
                    [field_name, "w2_wages"],
                    f"{field_name} is outside the expected range compared with Box 1 wages.",
                    "low",
                )
            )
    return issues


def _validate_tax_return(by_name: dict[str, ExtractedField]) -> list[ValidationIssue]:
    issues = []
    total_income = _value(by_name, "total_income")
    agi = _value(by_name, "agi")
    if agi is not None and total_income is not None and agi > total_income:
        issues.append(_issue(["agi", "total_income"], "AGI exceeds total income.", "high"))
    issues.extend(_validate_schedule_c(by_name))
    return issues


def _validate_schedule_c(by_name: dict[str, ExtractedField]) -> list[ValidationIssue]:
    issues = []
    net_profit = _first_value(
        by_name,
        ("schedule_c_net_profit", "schedule_c_business_1_net_profit"),
    )
    indexed_net_profit = _value(by_name, "schedule_c_business_1_net_profit")
    has_schedule_c = any(
        field.startswith("schedule_c") and item.value is not None
        for field, item in by_name.items()
    )
    if has_schedule_c and net_profit is None and indexed_net_profit is None:
        issues.append(
            _issue(
                ["schedule_c_net_profit"],
                "Schedule C net profit is missing.",
                "high",
            )
        )
    if net_profit is not None and indexed_net_profit is not None and abs(net_profit - indexed_net_profit) > 1:
        issues.append(
            _issue(
                ["schedule_c_net_profit", "schedule_c_business_1_net_profit"],
                "Schedule C net profit readings disagree.",
                "high",
            )
        )
    if net_profit is not None:
        for field_name in ("depreciation", "business_use_of_home"):
            field_aliases = (
                f"schedule_c_{field_name}",
                f"schedule_c_business_1_{field_name}",
            )
            if _first_value(by_name, field_aliases) is None:
                missing_field = field_aliases[0]
                if any(alias in by_name for alias in field_aliases):
                    missing_field = next(alias for alias in field_aliases if alias in by_name)
                issues.append(
                    _issue(
                        [missing_field],
                        f"{missing_field} may be a missing Schedule C add-back; verify against the form.",
                        "low",
                    )
                )
    return issues


def _first_value(
    by_name: dict[str, ExtractedField],
    field_names: tuple[str, ...],
) -> float | None:
    for field_name in field_names:
        if (value := _value(by_name, field_name)) is not None:
            return value
    return None


def _value(by_name: dict[str, ExtractedField], field_name: str) -> float | None:
    field = by_name.get(field_name)
    return field.value if field else None


def _issue(fields: list[str], message: str, severity: Severity) -> ValidationIssue:
    return {"fields": fields, "message": message, "severity": severity}


def _coerce_issue(issue: dict) -> ValidationIssue:
    severity = issue.get("severity")
    return _issue(
        list(issue.get("fields", [])),
        str(issue.get("message", "")),
        severity if severity in ("high", "low") else "low",
    )
