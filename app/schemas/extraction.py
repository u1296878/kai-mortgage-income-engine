from uuid import UUID

from pydantic import BaseModel


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class ExtractedField(BaseModel):
    field: str
    value: float
    document_id: UUID
    page: int
    bounding_box: BoundingBox
    raw_text: str | None = None
