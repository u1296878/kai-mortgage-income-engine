import re

from app.extractors.tax_return_block_index import TaxReturnBlockIndex
from app.extractors.tax_return_text import normalized_line_text
from app.extractors.w2_extractor import FIELD_PATTERNS

W2_CONTEXT_TOKENS = {
    **FIELD_PATTERNS,
    "w2_employer_name": ("employer", "name"),
    "w2_employee_name": ("employee", "name"),
}


def w2_context_blocks(field_name: str, blocks: list[dict]) -> list[dict]:
    index = TaxReturnBlockIndex(blocks)
    if field_name == "tax_year":
        return _tax_year_context(index) or blocks[:80]
    tokens = W2_CONTEXT_TOKENS.get(field_name)
    if tokens is None:
        return blocks
    matches = _matching_lines(index, tokens, 2)
    return [block for line in matches for block in line] or blocks[:80]


def _tax_year_context(index: TaxReturnBlockIndex) -> list[dict]:
    lines = []
    for line in index.unique_lines():
        text = normalized_line_text(line)
        if "form w 2" in text or "wage and tax statement" in text or "tax year" in text:
            lines.append(line)
        elif any(re.fullmatch(r"20\d{2}", block["text"]) for block in line):
            lines.append(line)
    return [block for line in _dedupe_lines(lines) for block in line]


def _matching_lines(
    index: TaxReturnBlockIndex,
    tokens: tuple[str, ...],
    window_size: int,
) -> list[list[dict]]:
    lines = sorted(index.unique_lines(), key=lambda line: (line[0]["page"], line[0]["y1"]))
    matches = []
    for position, line in enumerate(lines):
        text = normalized_line_text(line)
        if all(token in text for token in tokens):
            matches.extend(lines[position : position + window_size])
    return _dedupe_lines(matches)


def _dedupe_lines(lines: list[list[dict]]) -> list[list[dict]]:
    seen = set()
    unique = []
    for line in lines:
        key = (line[0]["page"], normalized_line_text(line))
        if key not in seen:
            unique.append(line)
            seen.add(key)
    return unique
