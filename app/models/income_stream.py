from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.income_stream_type import IncomeStreamType


class IncomeStream(Base):
    __tablename__ = "income_streams"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # TODO step 2b: remove ownership plumbing.
    broker_id: Mapped[str] = mapped_column(String(36), nullable=False)
    borrower_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    stream_type: Mapped[str] = mapped_column(
        String,
        default=IncomeStreamType.other.value,
        nullable=False,
    )
    annual_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
