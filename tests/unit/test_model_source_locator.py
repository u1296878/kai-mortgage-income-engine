from app.extractors.model_source_locator import locate_source


def test_locate_source_finds_numeric_block():
    source = locate_source(
        [{"text": "85,247", "page": 8, "x1": 1, "y1": 2, "x2": 3, "y2": 4}],
        85247,
        None,
    )

    assert source["text"] == "85,247"
