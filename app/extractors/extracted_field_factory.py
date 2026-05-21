from uuid import UUID

from app.schemas.extraction import BoundingBox, ExtractedField


def make_numeric_field(name: str, block: dict, document_id: UUID) -> ExtractedField:
    value = parse_float(block["text"])
    return make_field(name, value or 0.0, block, document_id)


def make_text_field(name: str, block: dict, document_id: UUID) -> ExtractedField:
    return make_field(name, 0.0, block, document_id, block.get("raw_text", block["text"]))


def make_field(
    name: str,
    value: float,
    block: dict,
    document_id: UUID,
    raw_text: str | None = None,
) -> ExtractedField:
    return ExtractedField(
        field=name,
        value=value,
        document_id=document_id,
        page=block["page"],
        bounding_box=BoundingBox(x1=block["x1"], y1=block["y1"], x2=block["x2"], y2=block["y2"]),
        raw_text=raw_text,
    )


def parse_float(text: str) -> float | None:
    clean_text = text.strip().replace("$", "").replace(",", "")
    try:
        return float(clean_text)
    except ValueError:
        return None
