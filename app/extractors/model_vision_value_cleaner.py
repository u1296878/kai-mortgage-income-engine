import re

from app.extractors.extracted_field_factory import parse_float

TEXT_FIELDS = {
    "w2_employer_name",
    "w2_employee_name",
    "paystub_period_end",
    "paystub_pay_frequency",
    "paystub_employer_name",
    "paystub_employee_name",
}


def clean_vision_entry(field_name: str, entry):
    if not isinstance(entry, dict) or field_name in TEXT_FIELDS:
        return entry
    cleaned_value = _clean_tax_year(entry.get("value")) if field_name == "tax_year" else _clean_number(entry.get("value"))
    cleaned_source = _clean_tax_year(_source_text(entry)) if field_name == "tax_year" else _clean_number_text(_source_text(entry))
    if cleaned_value is None and cleaned_source is None:
        return entry
    result = {**entry}
    if cleaned_value is not None:
        result["value"] = cleaned_value
        result["source_text"] = _format_number(cleaned_value)
    if cleaned_value is None and cleaned_source is not None:
        result["source_text"] = cleaned_source
    return result


def _clean_tax_year(value) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if not isinstance(value, str):
        return None
    match = re.search(r"\b(20\d{2})\b", value)
    return float(match.group(1)) if match else None


def _clean_number(value) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    text = _clean_number_text(value)
    return parse_float(text) if text else None


def _clean_number_text(value) -> str | None:
    if not isinstance(value, str):
        return None
    candidates = re.findall(r"\(?\$?-?\d[\d,]*(?:\.\d+)?\)?", value)
    parsed = [(candidate, parse_float(candidate)) for candidate in candidates]
    usable = [(candidate, number) for candidate, number in parsed if number is not None]
    if not usable:
        return None
    return _format_number(usable[-1][1])


def _source_text(entry: dict) -> str | None:
    return entry.get("source_text") or entry.get("text_value")


def _format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)
