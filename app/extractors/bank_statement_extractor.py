import re
from uuid import UUID

from app.exceptions import ExtractionFailed
from app.extractors.bank_statement_patterns import DATE_PATTERNS, DEPOSIT_KEYWORDS, EXCLUSION_KEYWORDS
from app.extractors.block_utils import line_for_block, merge_blocks
from app.extractors.date_utils import inclusive_month_count, iso_date, parse_date
from app.extractors.extracted_field_factory import make_field, parse_float
from app.schemas.extraction import ExtractedField


def extract_bank_statement_fields(blocks: list[dict], document_id: UUID) -> list[ExtractedField]:
    lines = _unique_lines(blocks)
    deposits = _deposit_amounts(lines)
    summary = _summary_deposit_amount(lines)
    if not deposits and not summary:
        raise ExtractionFailed("No qualifying bank statement deposits found")
    total_block = summary or _deposit_source_block(deposits)
    total = parse_float(total_block["text"]) if summary else sum(amount for amount, _block in deposits)
    months, month_block = _months_sampled(lines)
    average = (total or 0.0) / months
    fields = [
        make_field("average_monthly_deposit", average, total_block, document_id),
        make_field("months_sampled", float(months), month_block, document_id),
        make_field("total_deposits", total or 0.0, total_block, document_id),
    ]
    fields.extend(_date_fields(lines, document_id))
    return fields


def _deposit_amounts(lines: list[list[dict]]) -> list[tuple[float, dict]]:
    deposits = []
    for line in lines:
        text = _line_text(line)
        if not _is_deposit_line(text) or _is_excluded_line(text) or _is_summary_line(text):
            continue
        amount = _rightmost_amount(line)
        if amount and (value := parse_float(amount["text"])) is not None and value > 0:
            deposits.append((value, amount))
    return deposits


def _summary_deposit_amount(lines: list[list[dict]]) -> dict | None:
    for line in lines:
        text = _line_text(line)
        if _is_summary_line(text) and not _is_excluded_line(text):
            amount = _rightmost_amount(line)
            if amount and (value := parse_float(amount["text"])) is not None and value > 0:
                return amount
    return None


def _months_sampled(lines: list[list[dict]]) -> tuple[float, dict]:
    dates = _statement_dates(lines)
    if len(dates) >= 2:
        months = inclusive_month_count(dates[0][0], dates[1][0])
        if months:
            return float(months), merge_blocks([dates[0][1], dates[1][1]])
    transaction_months = {
        parsed.strftime("%Y-%m")
        for date_text, _block in _all_dates(lines)
        if (parsed := parse_date(date_text)) is not None
    }
    if transaction_months:
        return float(len(transaction_months)), _all_dates(lines)[0][1]
    return 1.0, lines[0][0]


def _date_fields(lines: list[list[dict]], document_id: UUID) -> list[ExtractedField]:
    dates = _statement_dates(lines)
    if len(dates) < 2:
        return []
    start_text = iso_date(dates[0][0]) or dates[0][0]
    end_text = iso_date(dates[1][0]) or dates[1][0]
    return [
        make_field("statement_start_date", 0.0, {**dates[0][1], "raw_text": start_text}, document_id, start_text),
        make_field("statement_end_date", 0.0, {**dates[1][1], "raw_text": end_text}, document_id, end_text),
    ]


def _statement_dates(lines: list[list[dict]]) -> list[tuple[str, dict]]:
    for line in lines:
        text = _line_text(line)
        if any(label in text for label in ("statement period", "statement dates", "for period", "from", "through")):
            dates = _dates_in_line(line)
            if len(dates) >= 2:
                return dates[:2]
    return []


def _all_dates(lines: list[list[dict]]) -> list[tuple[str, dict]]:
    return [date for line in lines for date in _dates_in_line(line)]


def _dates_in_line(line: list[dict]) -> list[tuple[str, dict]]:
    dates = []
    for block in line:
        for match in _date_matches(block["text"]):
            dates.append((match, block))
    line_text = " ".join(block["text"] for block in line)
    line_block = merge_blocks(line)
    for match in _date_matches(line_text):
        if match not in {date for date, _block in dates}:
            dates.append((match, line_block))
    return dates


def _date_matches(text: str) -> list[str]:
    matches = []
    for pattern in DATE_PATTERNS:
        matches.extend(re.findall(pattern, text))
    return matches


def _rightmost_amount(line: list[dict]) -> dict | None:
    amounts = [block for block in line if parse_float(block["text"]) is not None]
    return max(amounts, key=lambda block: block["x1"], default=None)


def _deposit_source_block(deposits: list[tuple[float, dict]]) -> dict:
    return max(deposits, key=lambda item: item[0])[1]


def _is_deposit_line(text: str) -> bool:
    return any(keyword in text for keyword in DEPOSIT_KEYWORDS)


def _is_excluded_line(text: str) -> bool:
    return any(keyword in text for keyword in EXCLUSION_KEYWORDS)


def _is_summary_line(text: str) -> bool:
    return "total deposits" in text or "deposits credits" in text


def _unique_lines(blocks: list[dict]) -> list[list[dict]]:
    lines = []
    seen = set()
    for block in blocks:
        key = (block["page"], round(block["y1"]))
        if key not in seen:
            seen.add(key)
            lines.append(sorted(line_for_block(blocks, block), key=lambda item: item["x1"]))
    return lines


def _line_text(line: list[dict]) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", " ".join(block["text"].lower() for block in line))).strip()
