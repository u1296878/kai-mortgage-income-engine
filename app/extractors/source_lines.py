from dataclasses import dataclass

from app.extractors.block_utils import merge_blocks

LINE_Y_TOLERANCE = 6.0


@dataclass(frozen=True)
class SourceLine:
    id: str
    page: int
    text: str
    raw_text: str
    blocks: list[dict]
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def bounding_box(self) -> dict:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass(frozen=True)
class SourceResolution:
    page: int | None
    bounding_box: dict | None
    raw_text: str | None
    invalid_ids: list[str]
    cross_page_ids: list[str]


def build_source_lines(blocks: list[dict]) -> list[SourceLine]:
    grouped = _group_visual_lines(blocks)
    return [_source_line(index, line) for index, line in enumerate(grouped, start=1)]


def format_source_lines(lines: list[SourceLine]) -> str:
    return "\n".join(f"[{line.id} p{line.page}] {line.raw_text}" for line in lines)


def resolve_source_lines(
    lines: list[SourceLine],
    source_line_ids: list[str],
) -> SourceResolution:
    by_id = {line.id: line for line in lines}
    selected = [by_id[source_id] for source_id in source_line_ids if source_id in by_id]
    invalid_ids = [source_id for source_id in source_line_ids if source_id not in by_id]
    if not selected:
        return SourceResolution(None, None, None, invalid_ids, [])
    pages = {line.page for line in selected}
    if len(pages) > 1:
        return SourceResolution(None, None, None, invalid_ids, [line.id for line in selected])
    merged = _merge_lines(selected)
    return SourceResolution(
        page=selected[0].page,
        bounding_box=_box(merged),
        raw_text="\n".join(line.raw_text for line in selected),
        invalid_ids=invalid_ids,
        cross_page_ids=[],
    )


def _group_visual_lines(blocks: list[dict]) -> list[list[dict]]:
    lines: list[list[dict]] = []
    for block in sorted(blocks, key=lambda item: (item["page"], item["y1"], item["x1"])):
        if lines and _same_visual_line(lines[-1], block):
            lines[-1].append(block)
        else:
            lines.append([block])
    return [sorted(line, key=lambda item: item["x1"]) for line in lines]


def _same_visual_line(line: list[dict], block: dict) -> bool:
    return line[0]["page"] == block["page"] and abs(line[0]["y1"] - block["y1"]) < LINE_Y_TOLERANCE


def _source_line(index: int, line: list[dict]) -> SourceLine:
    ordered = sorted(line, key=lambda item: item["x1"])
    merged = merge_blocks(ordered)
    return SourceLine(
        id=f"L{index:04d}",
        page=merged["page"],
        text=" ".join(block["text"] for block in ordered),
        raw_text=" ".join(block.get("raw_text", block["text"]) for block in ordered),
        blocks=ordered,
        x1=merged["x1"],
        y1=merged["y1"],
        x2=merged["x2"],
        y2=merged["y2"],
    )


def _merge_lines(lines: list[SourceLine]) -> dict:
    blocks = [
        {"text": line.raw_text, "page": line.page, **line.bounding_box}
        for line in lines
    ]
    return merge_blocks(blocks)


def _box(block: dict) -> dict:
    return {"x1": block["x1"], "y1": block["y1"], "x2": block["x2"], "y2": block["y2"]}
