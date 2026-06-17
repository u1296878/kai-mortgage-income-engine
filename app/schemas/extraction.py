from uuid import UUID

from pydantic import BaseModel


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class ExtractedField(BaseModel):
    field: str
    value: float | None
    document_id: UUID
    page: int | None
    bounding_box: BoundingBox | None
    raw_text: str | None = None
    confidence: float = 1.0
