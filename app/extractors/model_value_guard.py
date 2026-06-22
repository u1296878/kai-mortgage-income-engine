from dataclasses import dataclass

from app.extractors.extracted_field_factory import parse_float
from app.extractors.model_field_schemas import LINE_NUMBER_FIELDS, W2_BOX_FIELDS
from app.extractors.tax_return_block_index import TaxReturnBlockIndex
from app.extractors.tax_return_locator import line_anchors, nearest_money_value
from app.extractors.w2_extractor import FIELD_PATTERNS, _find_value_for_label

RECONCILED_LINE_FIELDS = {
    "schedule_c_net_profit",
    "total_income",
    "agi",
    "schedule_c_depreciation",
    "schedule_c_business_use_of_home",
}


@dataclass(frozen=True)
class GuardedValue:
    value: float | None
    review_flags: list[dict]


def corrected_value(field_name: str, value: float | None, blocks: list[dict]) -> float | None:
    return guarded_value(field_name, value, blocks).value


def guarded_value(field_name: str, value: float | None, blocks: list[dict]) -> GuardedValue:
    if field_name == "schedule_c_amortization_casualty" and not _mentions_amortization_or_casualty(blocks):
        return GuardedValue(None, [])
    if value is None:
        return GuardedValue(_anchored_value(field_name, blocks), [])
    if field_name in RECONCILED_LINE_FIELDS:
        return _reconciled_line_value(field_name, value, blocks)
    if field_name in W2_BOX_FIELDS and _same_value(value, W2_BOX_FIELDS[field_name]):
        fallback = _w2_box_value(field_name, blocks)
        return GuardedValue(fallback if fallback is not None else None, [])
    if value is None or field_name not in LINE_NUMBER_FIELDS:
        return GuardedValue(value, [])
    line_number, tokens = LINE_NUMBER_FIELDS[field_name]
    if not _same_value(value, line_number):
        return GuardedValue(value, [])
    fallback = _line_anchored_value(field_name, blocks)
    if fallback is not None and not _same_value(fallback, line_number):
        return GuardedValue(fallback, [])
    # Known model failure: blank form lines can be mistaken for their printed line label.
    return GuardedValue(None if _line_is_blank(blocks, line_number, tokens) else value, [])


def _reconciled_line_value(field_name: str, value: float, blocks: list[dict]) -> GuardedValue:
    line_number, _tokens = LINE_NUMBER_FIELDS[field_name]
    anchored = _line_money_value(field_name, blocks)
    if anchored is None:
        return GuardedValue(_legacy_line_value(field_name, value, blocks), [])
    if abs(anchored - value) <= 1:
        return GuardedValue(value, [])
    return GuardedValue(
        anchored,
        [
            {
                "fields": [field_name],
                "message": (
                    f"{field_name}: model read {_format_amount(value)} but Form line "
                    f"{line_number} shows {_format_amount(anchored)}; used the form value; verify."
                ),
                "severity": "high",
            }
        ],
    )


def _legacy_line_value(field_name: str, value: float, blocks: list[dict]) -> float | None:
    line_number, tokens = LINE_NUMBER_FIELDS[field_name]
    if not _same_value(value, line_number):
        return value
    return None if _line_is_blank(blocks, line_number, tokens) else value


def _format_amount(value: float) -> str:
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


def _line_is_blank(blocks: list[dict], line_number: str, tokens: tuple[str, ...]) -> bool:
    index = TaxReturnBlockIndex(blocks)
    anchors = line_anchors(index, line_number, tokens)
    return all(nearest_money_value(anchor, index, line_number) is None for anchor in anchors)


def _same_value(value: float, line_number: str) -> bool:
    normalized = line_number.rstrip("abcdefghijklmnopqrstuvwxyz")
    parsed = parse_float(normalized)
    return parsed is not None and abs(parsed - value) < 0.01


def _mentions_amortization_or_casualty(blocks: list[dict]) -> bool:
    text = " ".join(block["text"].lower() for block in blocks)
    return "amortization" in text or "casualty" in text


def _line_anchored_value(field_name: str, blocks: list[dict]) -> float | None:
    if field_name == "tax_year":
        return _first_year(blocks)
    if field_name == "schedule_c_business_miles":
        return _business_miles(blocks)
    if field_name in LINE_NUMBER_FIELDS:
        return _line_money_value(field_name, blocks)
    return None


def _anchored_value(field_name: str, blocks: list[dict]) -> float | None:
    if field_name in W2_BOX_FIELDS:
        return _w2_box_value(field_name, blocks)
    return _line_anchored_value(field_name, blocks)


def _w2_box_value(field_name: str, blocks: list[dict]) -> float | None:
    value = _find_value_for_label(blocks, FIELD_PATTERNS[field_name])
    return parse_float(value["text"]) if value else None


def _first_year(blocks: list[dict]) -> float | None:
    years = [parse_float(block["text"]) for block in blocks if block["text"].isdigit()]
    return next((year for year in years if year and 2000 <= year <= 2100), None)


def _business_miles(blocks: list[dict]) -> float | None:
    words = [block["text"] for block in blocks]
    for index, word in enumerate(words):
        if word.lower().strip(":") == "business":
            for candidate in words[index + 1 : index + 3]:
                value = parse_float(candidate)
                if value is not None:
                    return value
    return None


def _line_money_value(field_name: str, blocks: list[dict]) -> float | None:
    line_number, tokens = LINE_NUMBER_FIELDS[field_name]
    index = TaxReturnBlockIndex(blocks)
    for anchor in line_anchors(index, line_number, tokens):
        value = nearest_money_value(anchor, index, line_number)
        if value is not None:
            return parse_float(value["text"])
    return None
