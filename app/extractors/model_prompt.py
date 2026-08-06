from app.extractors.model_field_schemas import LINE_NUMBER_FIELDS
from app.extractors.source_lines import SourceLine, build_source_lines, format_source_lines
from app.extractors.tax_return_block_index import TaxReturnBlockIndex
from app.extractors.tax_return_locator import federal_form_pages, line_matches, schedule_c_pages
from app.extractors.tax_return_text import normalized_line_text


def tax_return_sections(blocks: list[dict]) -> dict[str, list[dict]]:
    index = TaxReturnBlockIndex(blocks)
    federal_pages = federal_form_pages(index)
    schedule_pages = _with_schedule_c_continuations(index, schedule_c_pages(index))
    return {
        "federal": _page_blocks(index, federal_pages),
        "schedule_c": _page_blocks(index, schedule_pages),
    }


def build_prompt(
    descriptions: dict[str, str],
    blocks: list[dict],
    source_lines: list[SourceLine] | None = None,
) -> str:
    fields = "\n".join(f"- {name}: {description}" for name, description in descriptions.items())
    return (
        "Extract mortgage income document fields from the OCR/text below.\n"
        "Return strict JSON matching the supplied schema. For each field, return "
        "value, confidence, source_text, and source_line_ids. Use source_line_ids "
        "from the bracketed IDs only, such as L0007. Do not invent IDs or return "
        "coordinates. Use numbers only, with no dollar signs or commas. A value "
        "printed as 94,380 must be returned as 94380, never 94. Each line has a "
        "printed line number (for example 12, 13, 31) that is a label, not a "
        "value. Never return a line number as the field value. Ignore amounts "
        "that belong to other line numbers. If a line has no numeric amount or "
        "the visible text is ambiguous, set its value to null and source_line_ids "
        "to []. Never compute income or infer missing values.\n\n"
        f"Fields:\n{fields}\n\nSource lines:\n{source_line_text(blocks, source_lines)}"
    )


def source_line_text(blocks: list[dict], source_lines: list[SourceLine] | None = None) -> str:
    return format_source_lines(source_lines or build_source_lines(blocks))


def page_text(blocks: list[dict]) -> str:
    index = TaxReturnBlockIndex(blocks)
    pages = sorted({block["page"] for block in blocks})
    sections = []
    for page in pages:
        lines = index.unique_lines({page})
        text = "\n".join(_line_text(line) for line in lines)
        sections.append(f"[page {page}]\n{text}")
    return "\n\n".join(sections)


def field_context_blocks(field_name: str, blocks: list[dict]) -> list[dict]:
    index = TaxReturnBlockIndex(blocks)
    if field_name == "tax_year":
        return _tax_year_blocks(index)
    if field_name == "schedule_c_amortization_casualty":
        return _matching_line_blocks(index, ("part v other expenses",), 5)
    if field_name not in LINE_NUMBER_FIELDS:
        return blocks
    line_number, tokens = LINE_NUMBER_FIELDS[field_name]
    return _line_window(index, line_number, tokens)


def _page_blocks(index: TaxReturnBlockIndex, pages: set[int]) -> list[dict]:
    return [
        block
        for page in sorted(pages)
        for block in index.page_blocks(page)
    ]


def _line_text(line: list[dict]) -> str:
    words = [block["text"] for block in sorted(line, key=lambda item: item["x1"])]
    collapsed = []
    for word in words:
        if not collapsed or collapsed[-1] != word:
            collapsed.append(word)
    return " ".join(collapsed)


def _with_schedule_c_continuations(index: TaxReturnBlockIndex, pages: set[int]) -> set[int]:
    all_pages = {block["page"] for block in index.blocks}
    continuation_pages = {
        page + 1
        for page in pages
        if page + 1 in all_pages and _page_has_schedule_c_continuation(index, page + 1)
    }
    return pages | continuation_pages


def _page_has_schedule_c_continuation(index: TaxReturnBlockIndex, page: int) -> bool:
    text = " ".join(_line_text(line).lower() for line in index.unique_lines({page}))
    return "part v other expenses" in text or "line 27a" in text or "44 of the total" in text


def _tax_year_blocks(index: TaxReturnBlockIndex) -> list[dict]:
    lines = _matching_lines(index, ("form 1040", "income tax return"), 1)
    year_blocks = [
        block
        for block in index.blocks
        if block["page"] in {word["page"] for line in lines for word in line}
        and block["text"].isdigit()
        and block["text"].startswith("20")
    ]
    return [block for line in lines for block in line] + year_blocks


def _matching_line_blocks(
    index: TaxReturnBlockIndex,
    needles: tuple[str, ...],
    window_size: int,
) -> list[dict]:
    return [block for line in _matching_lines(index, needles, window_size) for block in line]


def _matching_lines(
    index: TaxReturnBlockIndex,
    needles: tuple[str, ...],
    window_size: int,
) -> list[list[dict]]:
    lines = sorted(index.unique_lines(), key=lambda line: (line[0]["page"], line[0]["y1"]))
    matches = []
    for position, line in enumerate(lines):
        text = _line_text(line).lower()
        if any(needle in text for needle in needles):
            matches.extend(lines[position : position + window_size])
            break
    return _dedupe_lines(matches)


def _line_window(
    index: TaxReturnBlockIndex,
    line_number: str,
    tokens: tuple[str, ...],
) -> list[dict]:
    lines = sorted(index.unique_lines(), key=lambda line: (line[0]["page"], line[0]["y1"]))
    matches = []
    for position, line in enumerate(lines):
        if line_matches(normalized_line_text(line), line_number, tokens):
            matches.append((position, line))
    if not matches:
        return []
    position, _line = min(matches, key=lambda item: _line_match_rank(item[1], line_number))
    selected = _dedupe_lines(lines[position : position + 8])
    return [block for item in selected for block in item]


def _line_match_rank(line: list[dict], line_number: str) -> int:
    words = normalized_line_text(line).split()
    return 0 if words and words[0] == line_number else 1


def _dedupe_lines(lines: list[list[dict]]) -> list[list[dict]]:
    seen = set()
    unique = []
    for line in lines:
        key = (line[0]["page"], _line_text(line).lower())
        if key not in seen:
            unique.append(line)
            seen.add(key)
    return unique
