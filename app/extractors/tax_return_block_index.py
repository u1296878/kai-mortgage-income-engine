from app.extractors.tax_return_text import is_money, normalized_line_text


class TaxReturnBlockIndex:
    def __init__(self, blocks: list[dict]):
        self.blocks = blocks
        self._blocks_by_page = self._group_blocks_by_page(blocks)
        self._blocks_by_page_y = self._group_blocks_by_page_y(blocks)
        self._lines = self._build_lines(blocks)
        self._lines_by_page = self._group_lines_by_page(self._lines)
        self._label_lines = self._build_label_lines()

    def page_blocks(self, page: int) -> list[dict]:
        return self._blocks_by_page.get(page, [])

    def unique_lines(self, pages: set[int] | None = None) -> list[list[dict]]:
        if pages is None:
            return self._lines
        return [line for page in pages for line in self._lines_by_page.get(page, [])]

    def grouped_lines(self) -> dict[int, list[list[dict]]]:
        return self._lines_by_page

    def label_lines(self, pages: set[int] | None = None) -> list[tuple[list[dict], list[dict], str]]:
        if pages is None:
            return self._label_lines
        return [entry for entry in self._label_lines if entry[0][0]["page"] in pages]

    def _build_lines(self, blocks: list[dict]) -> list[list[dict]]:
        lines = []
        seen = set()
        for block in blocks:
            key = (block["page"], round(block["y1"]))
            if key in seen:
                continue
            seen.add(key)
            lines.append(self._line_for_block(block))
        return lines

    def _line_for_block(self, block: dict) -> list[dict]:
        nearby = self._nearby_y_blocks(block)
        return sorted(nearby, key=lambda item: item["x1"])

    def _build_label_lines(self) -> list[tuple[list[dict], list[dict], str]]:
        entries = []
        for line in self._lines:
            label_words = [block for block in line if not is_money(block["text"])]
            if label_words:
                entries.append((line, label_words, normalized_line_text(label_words)))
        return entries

    @staticmethod
    def _group_blocks_by_page(blocks: list[dict]) -> dict[int, list[dict]]:
        grouped: dict[int, list[dict]] = {}
        for block in blocks:
            grouped.setdefault(block["page"], []).append(block)
        return grouped

    @staticmethod
    def _group_lines_by_page(lines: list[list[dict]]) -> dict[int, list[list[dict]]]:
        grouped: dict[int, list[list[dict]]] = {}
        for line in lines:
            grouped.setdefault(line[0]["page"], []).append(line)
        return grouped

    @staticmethod
    def _group_blocks_by_page_y(blocks: list[dict]) -> dict[int, dict[int, list[dict]]]:
        grouped: dict[int, dict[int, list[dict]]] = {}
        for block in blocks:
            page = grouped.setdefault(block["page"], {})
            page.setdefault(round(block["y1"]), []).append(block)
        return grouped

    def _nearby_y_blocks(self, block: dict) -> list[dict]:
        page_y_blocks = self._blocks_by_page_y.get(block["page"], {})
        rounded_y = round(block["y1"])
        candidates = [
            item
            for y_bucket in range(rounded_y - 6, rounded_y + 7)
            for item in page_y_blocks.get(y_bucket, [])
        ]
        return [item for item in candidates if abs(item["y1"] - block["y1"]) < 6]


def as_tax_return_index(blocks: list[dict] | TaxReturnBlockIndex) -> TaxReturnBlockIndex:
    if isinstance(blocks, TaxReturnBlockIndex):
        return blocks
    return TaxReturnBlockIndex(blocks)
