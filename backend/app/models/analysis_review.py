from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ReviewDecision
from app.database.base import Base, IdMixin, TimestampMixin, utc_now


class AnalysisReview(Base, IdMixin, TimestampMixin):
    __tablename__ = "analysis_reviews"

    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_analyses.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    decision: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ReviewDecision.PENDING.value,
    )
    reviewer_name: Mapped[str] = mapped_column(String(120), nullable=False, default="demo-reviewer")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=utc_now,
    )

    analysis = relationship("IncidentAnalysis", back_populates="review")
