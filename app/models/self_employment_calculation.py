from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SelfEmploymentCalculation(Base):
    __tablename__ = "self_employment_calculations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # TODO step 2b: remove ownership plumbing.
    broker_id: Mapped[str] = mapped_column(String(36), nullable=False)
    borrower_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    qualifying_monthly: Mapped[float] = mapped_column(Float, nullable=False)
    annual_income: Mapped[float] = mapped_column(Float, nullable=False)
    included: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_business_key: Mapped[str | None] = mapped_column(String, nullable=True)
    breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
