from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AnalysisSeverity, AnalysisStatus
from app.database.base import Base, IdMixin, TimestampMixin


class IncidentAnalysis(Base, IdMixin, TimestampMixin):
    __tablename__ = "incident_analyses"

    analysis_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    video_asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("video_assets.id"),
        nullable=False,
        index=True,
    )
    processing_job_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("processing_jobs.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AnalysisStatus.QUEUED.value,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    incident_detected: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    incident_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detailed_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        default=AnalysisSeverity.NONE.value,
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommended_actions_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    limitations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inconclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    required_ppe_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observed_ppe_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    possibly_missing_ppe_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analysis_mode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    video_asset = relationship("VideoAsset", back_populates="analyses")
    processing_job = relationship("ProcessingJob")
    evidence_items = relationship(
        "AnalysisEvidence",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="AnalysisEvidence.timestamp_seconds",
    )
    review = relationship(
        "AnalysisReview",
        back_populates="analysis",
        cascade="all, delete-orphan",
        uselist=False,
    )
