from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmploymentCalculation(Base):
    __tablename__ = "employment_calculations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # broker_id is denormalized for scoping, exactly like IncomeStream.
    broker_id: Mapped[str] = mapped_column(String(36), nullable=False)
    borrower_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    # inputs: the EmploymentInput snapshot, so it can be re-displayed/audited.
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_monthly: Mapped[float] = mapped_column(Float, nullable=False)
    annual_income: Mapped[float] = mapped_column(Float, nullable=False)
    # breakdown: the per-bucket EmploymentResult, so display needs no recompute.
    breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
