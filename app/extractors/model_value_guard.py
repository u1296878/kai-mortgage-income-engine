from app.extractors.extracted_field_factory import parse_float
from app.extractors.model_field_schemas import LINE_NUMBER_FIELDS
from app.extractors.tax_return_block_index import TaxReturnBlockIndex
from app.extractors.tax_return_locator import line_anchors, nearest_money_value


def corrected_value(field_name: str, value: float | None, blocks: list[dict]) -> float | None:
    if field_name == "schedule_c_amortization_casualty" and not _mentions_amortization_or_casualty(blocks):
        return None
    if value is None:
        return _fallback_visible_value(field_name, blocks)
    if value is None or field_name not in LINE_NUMBER_FIELDS:
        return value
    line_number, tokens = LINE_NUMBER_FIELDS[field_name]
    if not _same_value(value, line_number):
        return value
    fallback = _fallback_visible_value(field_name, blocks)
    if fallback is not None and not _same_value(fallback, line_number):
        return fallback
    # Known model failure: blank form lines can be mistaken for their printed line label.
    return None if _line_is_blank(blocks, line_number, tokens) else value


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


def _fallback_visible_value(field_name: str, blocks: list[dict]) -> float | None:
    if field_name == "tax_year":
        return _first_year(blocks)
    if field_name == "schedule_c_business_miles":
        return _business_miles(blocks)
    if field_name in {
        "total_income",
        "agi",
        "schedule_c_net_profit",
        "schedule_c_depreciation",
        "schedule_c_business_use_of_home",
    }:
        return _line_money_value(field_name, blocks) or _last_money_value(blocks)
    return None


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


def _last_money_value(blocks: list[dict]) -> float | None:
    values = [
        value
        for block in blocks
        if "," in block["text"]
        for value in [parse_float(block["text"])]
        if value is not None
    ]
    return values[-1] if values else None


def _line_money_value(field_name: str, blocks: list[dict]) -> float | None:
    line_number = LINE_NUMBER_FIELDS[field_name][0]
    values = []
    matched = False
    for line in TaxReturnBlockIndex(blocks).unique_lines():
        first = _line_first_token(line)
        if matched and first and first != line_number:
            break
        if first == line_number:
            matched = True
        if matched:
            values.extend(_money_values(line))
    return values[-1] if values else None


def _line_first_token(line: list[dict]) -> str | None:
    text = sorted(line, key=lambda block: block["x1"])[0]["text"].lower().rstrip(".")
    return text if text[:1].isdigit() else None


def _money_values(blocks: list[dict]) -> list[float]:
    return [
        value
        for block in blocks
        if "," in block["text"]
        for value in [parse_float(block["text"])]
        if value is not None
    ]
