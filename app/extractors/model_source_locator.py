from app.extractors.block_utils import line_for_block, merge_blocks
from app.extractors.extracted_field_factory import parse_float


def locate_source(
    blocks: list[dict],
    value: float | None,
    source_text: str | None,
) -> dict | None:
    if value is not None:
        if source := next(
            (block for block in blocks if _same_number(parse_float(block["text"]), value)),
            None,
        ):
            return source
    if source_text:
        if source := _find_text_source(blocks, source_text):
            return source
    return None


def _find_text_source(blocks: list[dict], source_text: str) -> dict | None:
    needle = source_text.lower()
    for block in blocks:
        line = line_for_block(blocks, block)
        text = " ".join(word["text"] for word in line).lower()
        if needle in text:
            return {**merge_blocks(line), "raw_text": source_text}
    return None


def _same_number(left: float | None, right: float) -> bool:
    return left is not None and abs(left - right) < 0.01
