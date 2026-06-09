import re

from app.extractors.extracted_field_factory import parse_float


def normalized_line_text(blocks: list[dict]) -> str:
    return normalize(" ".join(block["text"] for block in blocks))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def is_money(text: str) -> bool:
    value = parse_float(text)
    if value is None:
        return False
    clean = text.strip().replace("$", "").replace(",", "")
    if re.fullmatch(r"\(?-?\d+\.\d{2}\)?", clean):
        return True
    return any(marker in text.strip() for marker in ("$", ",", "(", ")", "-")) or abs(value) >= 100
