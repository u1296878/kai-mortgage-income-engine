from app.extractors.source_lines import (
    build_source_lines,
    format_source_lines,
    resolve_source_lines,
)


def test_stable_ids_follow_page_y_x_order():
    lines = build_source_lines(
        [
            block("second", 1, 10, 30, 40, 40),
            block("third", 2, 10, 5, 20, 15),
            block("first", 1, 10, 10, 20, 20),
        ]
    )

    assert [(line.id, line.raw_text) for line in lines] == [
        ("L0001", "first"),
        ("L0002", "second"),
        ("L0003", "third"),
    ]


def test_words_on_same_visual_line_are_grouped_and_ordered_by_x():
    lines = build_source_lines(
        [
            block("income", 1, 30, 40, 60, 50),
            block("9", 1, 10, 41, 15, 50),
            block("Total", 1, 20, 39, 35, 50),
        ]
    )

    assert len(lines) == 1
    assert lines[0].text == "9 Total income"
    assert lines[0].raw_text == "9 Total income"


def test_source_lines_preserve_page_blocks_and_merged_box():
    lines = build_source_lines(
        [
            block("Total", 3, 10, 20, 30, 40),
            block("85,247", 3, 50, 22, 90, 42),
        ]
    )

    line = lines[0]
    assert line.page == 3
    assert line.blocks[0]["text"] == "Total"
    assert line.bounding_box == {"x1": 10, "y1": 20, "x2": 90, "y2": 42}


def test_format_source_lines_emits_prompt_text_with_ids_and_pages():
    lines = build_source_lines([block("9", 1, 10, 20, 20, 30), block("Total", 1, 25, 20, 50, 30)])

    assert format_source_lines(lines) == "[L0001 p1] 9 Total"


def test_resolving_single_valid_id_returns_page_box_and_raw_text():
    lines = build_source_lines([block("AGI", 2, 10, 20, 30, 40, raw_text="Adjusted gross income")])

    result = resolve_source_lines(lines, ["L0001"])

    assert result.page == 2
    assert result.bounding_box == {"x1": 10, "y1": 20, "x2": 30, "y2": 40}
    assert result.raw_text == "Adjusted gross income"
    assert result.invalid_ids == []
    assert result.cross_page_ids == []


def test_resolving_multiple_same_page_ids_merges_deterministically():
    lines = build_source_lines(
        [
            block("9 Total income", 1, 10, 20, 80, 30),
            block("85,247", 1, 100, 40, 140, 50),
        ]
    )

    result = resolve_source_lines(lines, ["L0001", "L0002"])

    assert result.page == 1
    assert result.bounding_box == {"x1": 10, "y1": 20, "x2": 140, "y2": 50}
    assert result.raw_text == "9 Total income\n85,247"


def test_invalid_ids_are_reported_without_crashing():
    lines = build_source_lines([block("visible", 1, 10, 20, 30, 40)])

    result = resolve_source_lines(lines, ["L9999", "not-an-id"])

    assert result.page is None
    assert result.bounding_box is None
    assert result.raw_text is None
    assert result.invalid_ids == ["L9999", "not-an-id"]


def test_cross_page_ids_are_detected():
    lines = build_source_lines([block("page one", 1, 10, 20, 30, 40), block("page two", 2, 10, 20, 30, 40)])

    result = resolve_source_lines(lines, ["L0001", "L0002"])

    assert result.page is None
    assert result.bounding_box is None
    assert result.cross_page_ids == ["L0001", "L0002"]


def test_same_blocks_produce_identical_output_across_runs():
    blocks = [
        block("b", 1, 40, 20, 50, 30),
        block("a", 1, 10, 20, 20, 30),
        block("c", 1, 10, 45, 20, 55),
    ]

    first = build_source_lines(blocks)
    second = build_source_lines(blocks)

    assert format_source_lines(first) == format_source_lines(second)
    assert [line.bounding_box for line in first] == [line.bounding_box for line in second]


def block(text: str, page: int, x1: float, y1: float, x2: float, y2: float, raw_text: str | None = None) -> dict:
    result = {"text": text, "page": page, "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    if raw_text is not None:
        result["raw_text"] = raw_text
    return result
