from app.extractors.extracted_field_factory import parse_float
from app.extractors.tax_return_locator import (
    line_anchors,
    nearest_money_value,
    normalized_line_text,
    unique_lines,
)


def find_line(blocks: list[dict], line_number: str, tokens: tuple[str, ...]) -> list[dict] | None:
    return next((line for line in unique_lines(blocks) if line_matches(line, line_number, tokens)), None)


def line_matches(line: list[dict], line_number: str, tokens: tuple[str, ...]) -> bool:
    words = normalized_line_text(line).split()
    return line_number in words and all(token in words for token in tokens)


def line_y(blocks: list[dict], line_number: str, tokens: tuple[str, ...]) -> float | None:
    line = find_line(blocks, line_number, tokens)
    return line[0]["y1"] if line else None


def amount_blocks(line: list[dict], min_x: float) -> list[dict]:
    return dedupe(
        [
            block
            for block in line
            if block["x1"] >= min_x and parse_float(block["text"]) is not None
        ],
    )


def nearest_column(block: dict, columns: dict[str, float]) -> str | None:
    return min(columns, key=lambda column: abs(block["x1"] - columns[column])) if columns else None


def line_value(blocks: list[dict], line_number: str, tokens: tuple[str, ...]) -> dict | None:
    line = find_line(blocks, line_number, tokens)
    values = amount_blocks(line, 320) if line else []
    return values[-1] if values else None


def continuation_value(
    blocks: list[dict],
    line_number: str,
    tokens: tuple[str, ...],
    pages: set[int],
) -> dict | None:
    values = [
        value
        for label in line_anchors(blocks, line_number, tokens, pages)
        if (value := nearest_money_value(label, blocks, line_number)) is not None
    ]
    return values[0] if values else None


def dedupe(blocks: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for block in blocks:
        key = (block["text"], round(block["x1"], 1), round(block["y1"], 1))
        if key not in seen:
            result.append(block)
            seen.add(key)
    return result
