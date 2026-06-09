from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.job_status import JobStatus


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(
        String,
        default=JobStatus.pending.value,
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    pages_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_done: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @property
    def percent(self) -> float:
        if self.status == JobStatus.complete.value:
            return 100.0
        if self.pages_total <= 0:
            return 0.0
        progress = (self.pages_done / self.pages_total) * 100
        return round(max(0.0, min(100.0, progress)), 2)
