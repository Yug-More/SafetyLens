from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin


class OperatorNotification(Base, IdMixin, TimestampMixin):
    """In-app operator alert for an analysis that requires human review."""

    __tablename__ = "operator_notifications"
    __table_args__ = (
        UniqueConstraint("analysis_id", name="uq_operator_notifications_analysis"),
    )

    notification_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incident_analyses.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("video_assets.id"), nullable=True
    )
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("incidents.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    incident_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    camera_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    camera_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unread", index=True)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    analysis = relationship("IncidentAnalysis")
    video_asset = relationship("VideoAsset")
    incident = relationship("Incident")
