import re
from uuid import UUID

from app.extractors.block_utils import distance, line_for_block, merge_blocks
from app.extractors.extracted_field_factory import make_field, make_numeric_field, parse_float
from app.extractors.tax_return_patterns import FILING_STATUSES, LINE_FIELDS
from app.exceptions import ExtractionFailed
from app.schemas.extraction import ExtractedField


def extract_tax_return_fields(blocks: list[dict], document_id: UUID) -> list[ExtractedField]:
    fields = []
    for field_name, (line_number, tokens) in LINE_FIELDS.items():
        value = _extract_line_value(blocks, line_number, tokens)
        if value:
            fields.append(make_numeric_field(field_name, value, document_id))
    schedule_c = _extract_schedule_c_net(blocks)
    tax_year = _find_tax_year(blocks)
    filing_status = _find_filing_status(blocks)
    if schedule_c:
        fields.append(make_numeric_field("schedule_c_net", schedule_c, document_id))
    if tax_year:
        fields.append(make_numeric_field("tax_year", tax_year, document_id))
    if filing_status:
        fields.append(make_field("filing_status", 0.0, filing_status, document_id, filing_status["raw_text"]))
    if not {field.field for field in fields} & {"agi", "total_income", "wages"}:
        raise ExtractionFailed("No Form 1040 income fields found")
    return fields


def _extract_line_value(blocks: list[dict], line_number: str, tokens: tuple[str, ...]) -> dict | None:
    values = [
        value
        for label in _line_anchors(blocks, line_number, tokens)
        if (value := _nearest_money_value(label, blocks)) is not None
    ]
    return values[0] if values else None


def _extract_schedule_c_net(blocks: list[dict]) -> dict | None:
    if not any("schedule c" in _line_text(line_for_block(blocks, block)) for block in blocks):
        return None
    return _extract_line_value(blocks, "31", ("net", "profit"))


def _line_anchors(blocks: list[dict], line_number: str, tokens: tuple[str, ...]) -> list[dict]:
    anchors = []
    seen = set()
    for line in _unique_lines(blocks):
        label_words = [block for block in line if not _is_money(block["text"])]
        text = _line_text(label_words)
        if _line_matches(text, line_number, tokens):
            key = (label_words[0]["page"], round(label_words[0]["y1"], 1), line_number)
            if key not in seen:
                anchors.append(merge_blocks(label_words))
                seen.add(key)
    return anchors


def _unique_lines(blocks: list[dict]) -> list[list[dict]]:
    lines = []
    seen = set()
    for block in blocks:
        key = (block["page"], round(block["y1"]))
        if key in seen:
            continue
        seen.add(key)
        lines.append(sorted(line_for_block(blocks, block), key=lambda item: item["x1"]))
    return lines


def _line_matches(text: str, line_number: str, tokens: tuple[str, ...]) -> bool:
    words = text.split()
    return line_number in words and all(token in words for token in tokens)


def _nearest_money_value(label: dict, blocks: list[dict]) -> dict | None:
    candidates = [
        block
        for block in blocks
        if _is_money(block["text"]) and _nearby_value(label, block)
    ]
    if not candidates:
        return None
    same_line = [block for block in candidates if abs(block["y1"] - label["y1"]) <= 5]
    if same_line:
        return max(same_line, key=lambda block: block["x1"])
    return min(candidates, key=lambda block: distance(label, block))


def _nearby_value(label: dict, block: dict) -> bool:
    if block["page"] != label["page"]:
        return False
    same_line = abs(block["y1"] - label["y1"]) <= 5 and block["x1"] >= label["x2"]
    below = 0 <= block["y1"] - label["y1"] <= 80 and abs(block["x1"] - label["x1"]) < 260
    return same_line or below


def _find_tax_year(blocks: list[dict]) -> dict | None:
    for line in _unique_lines(blocks):
        text = _line_text(line)
        if "form 1040" in text or "individual income tax return" in text:
            year = next((block for block in line if re.fullmatch(r"20\d{2}", block["text"])), None)
            if year:
                return year
    return next((block for block in blocks if re.fullmatch(r"20\d{2}", block["text"])), None)


def _find_filing_status(blocks: list[dict]) -> dict | None:
    for line in _unique_lines(blocks):
        text = _line_text(line)
        for status in FILING_STATUSES:
            if status in text:
                block = _status_block(line, status)
                return {**block, "raw_text": status}
    return None


def _status_block(line: list[dict], status: str) -> dict:
    words = set(status.split())
    matches = [block for block in line if _normalize(block["text"]) in words]
    return merge_blocks(matches) if matches else line[-1]


def _line_text(blocks: list[dict]) -> str:
    return _normalize(" ".join(block["text"] for block in blocks))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def _is_money(text: str) -> bool:
    value = parse_float(text)
    if value is None:
        return False
    clean_text = text.strip()
    has_money_marker = any(marker in clean_text for marker in ("$", ",", ".", "(", ")", "-"))
    return has_money_marker or abs(value) >= 100
