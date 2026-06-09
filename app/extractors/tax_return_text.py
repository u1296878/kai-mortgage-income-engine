import re

from app.extractors.block_utils import merge_blocks
from app.extractors.extracted_field_factory import parse_float


def normalized_line_text(blocks: list[dict]) -> str:
    return normalize(" ".join(block["text"] for block in blocks))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def line_matches(text: str, line_number: str, tokens: tuple[str, ...]) -> bool:
    words = text.split()
    return line_number in words and all(token in words for token in tokens)


def is_money(text: str) -> bool:
    value = parse_float(text)
    if value is None:
        return False
    clean = text.strip().replace("$", "").replace(",", "")
    if re.fullmatch(r"\(?-?\d+\.\d{2}\)?", clean):
        return True
    return any(marker in text.strip() for marker in ("$", ",", "(", ")", "-")) or abs(value) >= 100


def continuation_label_matches(
    lines: list[list[dict]],
    index: int,
    line_number: str,
    tokens: tuple[str, ...],
) -> bool:
    line = lines[index]
    if not line_number_blocks(line, line_number):
        return False
    words = [block for block in line if not is_money(block["text"])]
    base_y = line[0]["y1"]
    for next_line in lines[index + 1 :]:
        if next_line[0]["page"] != line[0]["page"] or next_line[0]["y1"] - base_y > 45:
            break
        if line_number_blocks(next_line, line_number) or starts_new_numbered_line(next_line):
            break
        words.extend(block for block in next_line if not is_money(block["text"]))
        if line_matches(normalized_line_text(words), line_number, tokens):
            return True
    return False


def line_anchor(label_words: list[dict], line_number: str) -> dict:
    anchor = merge_blocks(label_words)
    line_numbers = line_number_blocks(label_words, line_number)
    number_block = line_numbers[0] if line_numbers else label_words[0]
    return {
        **anchor,
        "line_y1": number_block["y1"],
        "line_number_x2": number_block["x2"],
    }


def line_number_blocks(line: list[dict], line_number: str) -> list[dict]:
    return [block for block in line if normalize(block["text"]) == line_number]


def starts_new_numbered_line(line: list[dict]) -> bool:
    first = line[0]
    return first["x1"] < 90 and re.fullmatch(r"\d+[a-z]?", normalize(first["text"])) is not None
