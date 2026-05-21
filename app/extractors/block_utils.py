import re


def line_for_block(blocks: list[dict], block: dict) -> list[dict]:
    return [
        candidate
        for candidate in blocks
        if candidate["page"] == block["page"] and abs(candidate["y1"] - block["y1"]) < 6
    ]


def line_text(blocks: list[dict], block: dict) -> str:
    return " ".join(word["text"].lower() for word in line_for_block(blocks, block))


def merge_blocks(blocks: list[dict]) -> dict:
    return {
        "text": " ".join(block["text"] for block in blocks),
        "page": blocks[0]["page"],
        "x1": min(block["x1"] for block in blocks),
        "y1": min(block["y1"] for block in blocks),
        "x2": max(block["x2"] for block in blocks),
        "y2": max(block["y2"] for block in blocks),
    }


def is_numeric(text: str) -> bool:
    return re.fullmatch(r"\$?[\d,]+(\.\d{2})?", text.strip()) is not None


def is_amount(text: str) -> bool:
    clean_text = text.strip().replace("$", "").replace(",", "")
    if not is_numeric(text):
        return False
    return "." in clean_text or float(clean_text) >= 100


def is_right_or_below(label: dict, block: dict) -> bool:
    same_page = block["page"] == label["page"]
    right = block["x1"] >= label["x2"] and abs(block["y1"] - label["y1"]) < 40
    below = 0 <= block["y1"] - label["y1"] < 80 and abs(block["x1"] - label["x1"]) < 240
    return same_page and (right or below)


def distance(label: dict, block: dict) -> float:
    return abs(block["x1"] - label["x1"]) + abs(block["y1"] - label["y1"])
