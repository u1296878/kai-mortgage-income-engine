import re

from app.extractors.block_utils import line_for_block, merge_blocks
from app.extractors.extracted_field_factory import parse_float
from app.extractors.tax_return_patterns import FILING_STATUSES, LINE_FIELDS


def line_anchors(blocks: list[dict], line_number: str, tokens: tuple[str, ...], pages: set[int] | None = None) -> list[dict]:
    anchors: list[dict] = []
    seen = set()
    for line in unique_lines(blocks):
        if pages and line[0]["page"] not in pages:
            continue
        label_words = [block for block in line if not is_money(block["text"])]
        if label_words and line_matches(normalized_line_text(label_words), line_number, tokens):
            key = (label_words[0]["page"], round(label_words[0]["y1"], 1), line_number)
            if key not in seen:
                anchors.append(merge_blocks(label_words))
                seen.add(key)
    return anchors


def nearest_money_value(label: dict, blocks: list[dict], line_number: str | None = None) -> dict | None:
    candidates = [block for block in blocks if is_money(block["text"]) and nearby_value(label, block) and value_candidate(label, block)]
    if not candidates:
        return None
    same_line = [block for block in candidates if abs(block["y1"] - label["y1"]) <= 5]
    if same_line:
        return max(same_line, key=lambda block: block["x1"])
    if line_number:
        return continuation_line_value(label, blocks, line_number)
    return None


def continuation_line_value(label: dict, blocks: list[dict], line_number: str) -> dict | None:
    lines = [
        line
        for line in unique_lines(blocks)
        if line[0]["page"] == label["page"] and 0 < line[0]["y1"] - label["y1"] <= 90
    ]
    for line in sorted(lines, key=lambda items: items[0]["y1"]):
        line_numbers = [block for block in line if normalize(block["text"]) == line_number]
        if not any(block["x1"] >= label["x2"] for block in line_numbers):
            continue
        values = [block for block in line if is_money(block["text"]) and block["x1"] >= label["x2"]]
        if values:
            return max(values, key=lambda block: block["x1"])
    return None


def find_tax_year(blocks: list[dict], federal_pages: set[int]) -> dict | None:
    for line in candidate_lines(blocks, federal_pages):
        text = normalized_line_text(line)
        if "form 1040" in text or "individual income tax return" in text:
            year = next((block for block in line if re.fullmatch(r"20\d{2}", block["text"])), None)
            if year:
                return year
    return next((block for block in blocks if (not federal_pages or block["page"] in federal_pages) and re.fullmatch(r"20\d{2}", block["text"])), None)


def find_filing_status(blocks: list[dict], federal_pages: set[int]) -> dict | None:
    for line in candidate_lines(blocks, federal_pages):
        text = normalized_line_text(line)
        for status in FILING_STATUSES:
            if status in text:
                return {**status_block(line, status), "raw_text": status}
    return None


def federal_form_pages(blocks: list[dict]) -> set[int]:
    lines_by_page = grouped_lines(blocks)
    if not lines_by_page:
        return set()
    best_page, best_score = max(((page, federal_page_score(lines)) for page, lines in lines_by_page.items()), key=lambda item: item[1])
    return {best_page} if best_score > 0 else set()


def schedule_c_pages(blocks: list[dict]) -> set[int]:
    return {page for page, lines in grouped_lines(blocks).items() if schedule_c_page_score(lines) > 0}


def grouped_lines(blocks: list[dict]) -> dict[int, list[list[dict]]]:
    grouped: dict[int, list[list[dict]]] = {}
    for line in unique_lines(blocks):
        grouped.setdefault(line[0]["page"], []).append(line)
    return grouped


def unique_lines(blocks: list[dict]) -> list[list[dict]]:
    lines = []
    seen = set()
    for block in blocks:
        key = (block["page"], round(block["y1"]))
        if key not in seen:
            seen.add(key)
            lines.append(sorted(line_for_block(blocks, block), key=lambda item: item["x1"]))
    return lines


def candidate_lines(blocks: list[dict], pages: set[int]) -> list[list[dict]]:
    lines = unique_lines(blocks)
    return [line for line in lines if line[0]["page"] in pages] if pages else lines


def federal_page_score(lines: list[list[dict]]) -> int:
    page_text = " ".join(normalized_line_text(line) for line in lines)
    score = (2 if "form 1040" in page_text else 0) + (3 if "individual income tax return" in page_text else 0)
    if any("filing status" in normalized_line_text(line) for line in lines):
        score += 1
    for line_number, tokens in LINE_FIELDS.values():
        if page_has_line_anchor(lines, line_number, tokens):
            score += 4
    return score


def schedule_c_page_score(lines: list[list[dict]]) -> int:
    header_text = " ".join(normalized_line_text(line) for line in lines[:15])
    score = 3 if "schedule c" in header_text and "profit or loss from business" in header_text else 0
    if score and page_has_line_anchor(lines, "31", ("net", "profit")):
        score += 4
    return score


def page_has_line_anchor(lines: list[list[dict]], line_number: str, tokens: tuple[str, ...]) -> bool:
    for line in lines:
        label_words = [block for block in line if not is_money(block["text"])]
        if label_words and line_matches(normalized_line_text(label_words), line_number, tokens):
            return True
    return False


def line_matches(text: str, line_number: str, tokens: tuple[str, ...]) -> bool:
    words = text.split()
    return line_number in words and all(token in words for token in tokens)


def normalized_line_text(blocks: list[dict]) -> str:
    return normalize(" ".join(block["text"] for block in blocks))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def status_block(line: list[dict], status: str) -> dict:
    words = set(status.split())
    matches = [block for block in line if normalize(block["text"]) in words]
    return merge_blocks(matches) if matches else line[-1]


def is_money(text: str) -> bool:
    value = parse_float(text)
    if value is None:
        return False
    clean = text.strip().replace("$", "").replace(",", "")
    if re.fullmatch(r"\(?-?\d+\.\d{2}\)?", clean):
        return True
    return any(marker in text.strip() for marker in ("$", ",", "(", ")", "-")) or abs(value) >= 100


def value_candidate(label: dict, block: dict) -> bool:
    return block["x1"] >= label["x2"] + 20 if abs(block["y1"] - label["y1"]) <= 5 else block["x1"] >= label["x1"] + 20


def nearby_value(label: dict, block: dict) -> bool:
    if block["page"] != label["page"]:
        return False
    same_line = abs(block["y1"] - label["y1"]) <= 5 and block["x1"] >= label["x2"]
    below = 0 <= block["y1"] - label["y1"] <= 260 and block["x1"] >= label["x1"]
    return same_line or below
