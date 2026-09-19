from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin


class DetectorEventIngestion(Base, IdMixin, TimestampMixin):
    """Maps Sean's detector event_id to application video/analysis artifacts."""

    __tablename__ = "detector_event_ingestions"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_detector_event_ingestions_event_id"),
    )

    event_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, default="possible_person_down")
    source_id: Mapped[str] = mapped_column(String(120), nullable=False)
    camera_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cameras.id"), nullable=True
    )
    track_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_timestamp_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    clip_event_offset_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    detector_state: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    trigger_signals_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    pose_quality: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    heuristic_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="received", index=True)
    location: Mapped[str] = mapped_column(String(200), nullable=False, default="Loading Zone B")
    video_asset_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("video_assets.id"), nullable=True
    )
    processing_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("processing_jobs.id"), nullable=True
    )
    analysis_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("incident_analyses.id"), nullable=True
    )
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("incidents.id"), nullable=True
    )
    error_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    camera = relationship("Camera")
    video_asset = relationship("VideoAsset")
    processing_job = relationship("ProcessingJob")
    analysis = relationship("IncidentAnalysis")
    incident = relationship("Incident")
