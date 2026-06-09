from time import perf_counter

from app.extractors.block_utils import line_for_block
from app.extractors.tax_return_block_index import TaxReturnBlockIndex
from app.extractors.tax_return_locator import line_anchors, nearest_money_value, unique_lines
from tests.unit.tax_return_test_helpers import block, schedule_c_blocks, schedule_e_blocks, tax_return_blocks


def test_indexed_unique_lines_match_legacy_grouping():
    blocks = tax_return_blocks() + schedule_c_blocks() + schedule_e_blocks()

    result = unique_lines(TaxReturnBlockIndex(blocks))

    assert result == _legacy_unique_lines(blocks)


def test_preindexed_lookup_matches_raw_block_lookup():
    blocks = tax_return_blocks() + schedule_e_blocks()
    index = TaxReturnBlockIndex(blocks)

    raw_anchor = line_anchors(blocks, "11", ("adjusted", "gross"))[0]
    indexed_anchor = line_anchors(index, "11", ("adjusted", "gross"))[0]
    raw_value = nearest_money_value(raw_anchor, blocks, "11")
    indexed_value = nearest_money_value(indexed_anchor, index, "11")

    assert indexed_anchor == raw_anchor
    assert indexed_value == raw_value


def test_shared_index_reuses_line_grouping_for_repeated_anchor_lookups():
    blocks = _large_tax_return_blocks()
    index = TaxReturnBlockIndex(blocks)

    raw_started_at = perf_counter()
    for _ in range(20):
        line_anchors(blocks, "11", ("adjusted", "gross"))
    raw_duration = perf_counter() - raw_started_at

    indexed_started_at = perf_counter()
    for _ in range(20):
        line_anchors(index, "11", ("adjusted", "gross"))
    indexed_duration = perf_counter() - indexed_started_at

    assert indexed_duration < raw_duration * 0.5


def _legacy_unique_lines(blocks: list[dict]) -> list[list[dict]]:
    lines = []
    seen = set()
    for item in blocks:
        key = (item["page"], round(item["y1"]))
        if key not in seen:
            seen.add(key)
            lines.append(sorted(line_for_block(blocks, item), key=lambda candidate: candidate["x1"]))
    return lines


def _large_tax_return_blocks() -> list[dict]:
    blocks = []
    for page in range(1, 31):
        for row in range(80):
            y = 40 + row * 7
            line_number = "11" if row == 40 else str(row)
            label = ("Adjusted", "gross", "income") if row == 40 else ("filler", "line", str(row))
            blocks.append(block(line_number, 50, y, 66, y + 10, page=page))
            for index, text in enumerate(label):
                blocks.append(block(text, 80 + index * 50, y, 120 + index * 50, y + 10, page=page))
            blocks.append(block(f"{1000 + row}.00", 500, y, 560, y + 10, page=page))
    return blocks
